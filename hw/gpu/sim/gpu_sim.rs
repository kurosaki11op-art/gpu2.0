// Functional simulator of our GPU's tile mesh with a time and energy model, milestones M1 and M2 (31 Oct 2026). Instruction set: hw/gpu/ISA_M1.md. Standard library only. Build: rustc -O gpu_sim.rs
// usage: gpu_sim DIR MODE NSAMPLES [TILE_BYTES [decode]]      MODE = fp32 | w8 | int8
// reads DIR/{manifest.txt, tensors.bin, program.txt, inputs.bin, input.txt}; writes DIR/out_MODE.bin (outputs of the last MM, f32) and DIR/counters_MODE.json.
// Without "decode": NSAMPLES independent inputs, counters of sample 0. With "decode": NSAMPLES decode steps, tensors `tokid` (from inputs.bin) and `posn` (step index) set before each step, KV caches persist across steps, counters are totals over all steps.
// Time model (M2): per instruction cycles = ceil(max(multiply-adds / MACPC, SRAM bytes / SRAMBW, vector ops / VECL)) + network cycles; weight loading is not timed. Energy model: pJ per multiply-add, SRAM byte, vector op, mesh byte-hop; static power added over the elapsed cycles.
use std::collections::HashMap;
use std::fs;
use std::io::Write;

// ASSUMED parameters, from the wafer-scale cost and energy notes (see hw/gpu/M2_plan.md)
const MACPC: f64 = 368.0; const SRAMBW: f64 = 2000.0; const VECL: f64 = 64.0; fn env_u64(k: &str, d: u64) -> u64 { std::env::var(k).ok().and_then(|v| v.parse().ok()).unwrap_or(d) }
fn linkbw() -> u64 { static V: std::sync::OnceLock<u64> = std::sync::OnceLock::new(); *V.get_or_init(|| env_u64("GPU_LINKBW", 64)) } // bytes per cycle per link (ASSUMED)
fn hopcyc() -> u64 { static V: std::sync::OnceLock<u64> = std::sync::OnceLock::new(); *V.get_or_init(|| env_u64("GPU_HOPCYC", 2)) } // cycles per hop (ASSUMED)
const CLOCK_HZ: f64 = 1.0e9;
const E_MAC_PJ: f64 = 0.25; const E_SRAM_BYTE_PJ: f64 = 0.55 * 8.0; const E_VEC_PJ: f64 = 0.4; const E_HOP_BYTE_PJ: f64 = 0.1 * 8.0; const LEAK_W_PER_GB: f64 = 1.6;

#[derive(Clone)]
struct Tn { dims: Vec<usize>, d: Vec<f32>, home: usize }
struct Wq { q: Vec<i8>, s: Vec<f32>, k: usize, n: usize }
#[derive(Default, Clone)]
struct Ct { macs: u64, macs16: u64, rd: u64, wr: u64, hop: u64, vec: u64, net: u64 }
impl Ct { fn diff(&self, b: &Ct) -> Ct { Ct { macs: self.macs - b.macs, macs16: self.macs16 - b.macs16, rd: self.rd - b.rd, wr: self.wr - b.wr, hop: self.hop - b.hop, vec: self.vec - b.vec, net: self.net - b.net } } }

fn numel(d: &[usize]) -> usize { d.iter().product() }
fn dist(a: usize, b: usize, side: usize) -> u64 { let (ax, ay, bx, by) = ((a % side) as i64, (a / side) as i64, (b % side) as i64, (b / side) as i64); ((ax - bx).abs() + (ay - by).abs()) as u64 }

struct Sim { t: HashMap<String, Tn>, wq: HashMap<String, Wq>, prec: HashMap<String, u8>, int8: bool, a8: bool, side: usize, tile_bytes: usize, used: HashMap<usize, usize>, ct: HashMap<String, Ct>, tag: String, cyc: HashMap<String, f64>, en: HashMap<String, f64>, stripe: usize, ltiles: usize, striped: std::collections::HashSet<String>, ovr: Option<f64>, macpc: f64, srambw: f64, stripe_attn: bool, compact: bool }
impl Sim {
    // placement of stripe tiles. Spread (default): stripe i of logical tile h is tile h + i*ltiles on a square mesh. Compact (GPU_COMPACT=1): the `stripe` tiles of logical tile h form a w x w block (w = ceil(sqrt(stripe))), the home tile is the block's corner, blocks sit side by side.
    fn cpos(&self, id: usize) -> (i64, i64) { let s = self.stripe.max(1); let w = (s as f64).sqrt().ceil() as usize; let bx = ((self.ltiles as f64).sqrt().ceil() as usize).max(1); let (g, i) = (id / s, id % s); (((g % bx) * w + i % w) as i64, ((g / bx) * w + i / w) as i64) }
    fn stripe_id(&self, h: usize, i: usize) -> usize { if self.compact { h * self.stripe + i } else { h + i * self.ltiles } }
    fn hd(&self, a: usize, b: usize) -> u64 { if self.compact { let (p, q) = (self.cpos(a * self.stripe), self.cpos(b * self.stripe)); ((p.0 - q.0).abs() + (p.1 - q.1).abs()) as u64 } else { dist(a, b, self.side) } }
    fn sd(&self, h: usize, i: usize) -> u64 { if self.compact { let (p, q) = (self.cpos(h * self.stripe), self.cpos(h * self.stripe + i)); ((p.0 - q.0).abs() + (p.1 - q.1).abs()) as u64 } else { dist(h, h + i * self.ltiles, self.side) } }
    fn wb(&self) -> u64 { if self.int8 { 1 } else { 4 } }
    fn ab(&self) -> u64 { if self.int8 { 2 } else { 4 } }
    fn c(&mut self) -> &mut Ct { let tag = self.tag.clone(); self.ct.entry(tag).or_default() }
    fn get(&self, n: &str) -> Tn { self.t.get(n).unwrap_or_else(|| panic!("missing tensor {}", n)).clone() }
    fn fetch(&mut self, n: &str, tile: usize) -> Tn {
        let t = self.get(n); let h = self.hd(t.home, tile); let ab = self.ab(); let bytes = numel(&t.dims) as u64 * ab;
        self.c().hop += bytes * h; self.c().rd += bytes; if h > 0 { self.c().net += bytes / linkbw() + hopcyc() *h; } t
    }
    fn put(&mut self, n: &str, dims: Vec<usize>, d: Vec<f32>, home: usize) { let ab = self.ab(); self.c().wr += d.len() as u64 * ab; self.t.insert(n.to_string(), Tn { dims, d, home }); }
    // matrix product a[m,k] @ w[k,n]; int8: per-row activation scale, per-column weight scale, integer accumulate; precision of the activations per weight: 8 (default), 16, 0 (FP32, also the whole mode w8)
    fn mm(&mut self, wname: &str, a: &[f32], m: usize, k: usize) -> Vec<f32> {
        let (n, out); let mut m16 = false;
        if self.int8 {
            let w = &self.wq[wname]; assert_eq!(w.k, k); n = w.n; let mut o = vec![0f32; m * n];
            let p = if !self.a8 { 0 } else { *self.prec.get(wname).unwrap_or(&8) };
            if p == 0 {
                for i in 0..m { for kk in 0..k { let x = a[i * k + kk]; let wr = &w.q[kk * n..(kk + 1) * n]; for j in 0..n { o[i * n + j] += x * (wr[j] as f32 * w.s[j]); } } }
            } else if p == 16 {
                m16 = true;
                for i in 0..m {
                    let row = &a[i * k..(i + 1) * k]; let mx = row.iter().fold(0f32, |x, &v| x.max(v.abs())); let sa = if mx > 0.0 { mx / 32767.0 } else { 1.0 };
                    let qa: Vec<i64> = row.iter().map(|&v| (v / sa).round().clamp(-32767.0, 32767.0) as i64).collect(); let mut acc = vec![0i64; n];
                    for kk in 0..k { let x = qa[kk]; if x == 0 { continue; } let wr = &w.q[kk * n..(kk + 1) * n]; for j in 0..n { acc[j] += x * wr[j] as i64; } }
                    for j in 0..n { o[i * n + j] = acc[j] as f32 * sa * w.s[j]; }
                }
            } else {
                for i in 0..m {
                    let row = &a[i * k..(i + 1) * k]; let mx = row.iter().fold(0f32, |x, &v| x.max(v.abs())); let sa = if mx > 0.0 { mx / 127.0 } else { 1.0 };
                    let qa: Vec<i32> = row.iter().map(|&v| (v / sa).round().clamp(-127.0, 127.0) as i32).collect(); let mut acc = vec![0i32; n];
                    for kk in 0..k { let x = qa[kk]; if x == 0 { continue; } let wr = &w.q[kk * n..(kk + 1) * n]; for j in 0..n { acc[j] += x * wr[j] as i32; } }
                    for j in 0..n { o[i * n + j] = acc[j] as f32 * sa * w.s[j]; }
                }
            }
            out = o;
        } else {
            let w = self.t.get(wname).unwrap(); n = w.dims[1]; let mut o = vec![0f32; m * n];
            for i in 0..m { for kk in 0..k { let x = a[i * k + kk]; let wr = &w.d[kk * n..(kk + 1) * n]; for j in 0..n { o[i * n + j] += x * wr[j]; } } }
            out = o;
        }
        let wbytes = self.wb(); self.c().macs += (m * k * n) as u64; if m16 { self.c().macs16 += (m * k * n) as u64; } self.c().rd += (k * n) as u64 * wbytes; out
    }
    fn mmop(&mut self, out: &str, an: &str, wn: &str, bn: &str, tile: usize) {
        assert_eq!(self.t[wn].home, tile, "weight {} is not homed on tile {}", wn, tile);
        let a = self.fetch(an, tile); let k = *self.t[wn].dims.first().unwrap(); let m = a.d.len() / k;
        let mut o; let n;
        if self.stripe > 1 && self.striped.contains(wn) {
            // striped: the output columns of this weight are split over `stripe` tiles (stripe i lives on tile home + i*ltiles); the activation is broadcast, the outputs are gathered on the home tile
            let sn = self.stripe; let parts: Vec<String> = (0..sn).map(|i| format!("{}#{}", wn, i)).filter(|nm| self.wq.contains_key(nm) || self.t.contains_key(nm)).collect();
            let ab = self.ab(); let abytes = (m * k) as u64 * ab; let mut cols: Vec<Vec<f32>> = Vec::new(); let mut worst = 0f64; let mut maxd = 0u64; let mut tot_n = 0;
            for (i, nm) in parts.iter().enumerate() {
                let before = self.c().clone(); let part = self.mm(nm, &a.d, m, k); let ni = part.len() / m; tot_n += ni;
                let dd = self.sd(tile, i); maxd = maxd.max(dd);
                self.c().hop += abytes * dd + (m * ni) as u64 * ab * dd; // broadcast in, gather out
                let d = self.c().diff(&before); let mc = (d.macs + d.macs16) as f64;
                worst = worst.max((mc / self.macpc).max(d.rd as f64 / self.srambw).ceil());
                cols.push(part);
            }
            n = tot_n; o = vec![0f32; m * n]; let mut c0 = 0;
            for part in &cols { let ni = part.len() / m; for r in 0..m { for j in 0..ni { o[r * n + c0 + j] = part[r * ni + j]; } } c0 += ni; }
            let bc = abytes / linkbw() + hopcyc() *maxd; let ga = (m * n) as u64 * ab / linkbw() + hopcyc() *maxd;
            self.ovr = Some(worst + (bc + ga) as f64);
        } else { o = self.mm(wn, &a.d, m, k); n = o.len() / m; }
        if bn != "-" { let b = self.t[bn].d.clone(); for i in 0..m { for j in 0..n { o[i * n + j] += b[j]; } } self.c().vec += (m * n) as u64; }
        let mut dims = a.dims.clone(); *dims.last_mut().unwrap() = n; if dims.len() == 1 { dims = vec![m, n]; } self.put(out, dims, o, tile);
    }
    fn conv(&mut self, out: &str, x: &str, wn: &str, bn: &str, cin: usize, kh: usize, kw: usize, tile: usize) {
        let t = self.fetch(x, tile); let (h, w) = (t.dims[2], t.dims[3]); let (oh, ow) = (h - kh + 1, w - kw + 1); let kdim = cin * kh * kw; let mut patches = vec![0f32; oh * ow * kdim];
        for y in 0..oh { for xx in 0..ow { let r = y * ow + xx; let mut q = 0; for c in 0..cin { for dy in 0..kh { for dx in 0..kw { patches[r * kdim + q] = t.d[(c * h + y + dy) * w + xx + dx]; q += 1; } } } } }
        let o = self.mm(wn, &patches, oh * ow, kdim); let cout = o.len() / (oh * ow); let b = self.t[bn].d.clone(); let mut res = vec![0f32; cout * oh * ow];
        for r in 0..oh * ow { for c in 0..cout { res[c * oh * ow + r] = o[r * cout + c] + b[c]; } } self.c().vec += (oh * ow * cout) as u64; self.put(out, vec![1, cout, oh, ow], res, tile);
    }
    fn attn(&mut self, out: &str, q: &str, k: &str, v: &str, heads: usize, tile: usize) {
        let (qt, kt, vt) = (self.fetch(q, tile), self.fetch(k, tile), self.fetch(v, tile)); let (t, d) = (qt.dims[0], qt.dims[1]); let dh = d / heads; let sc = 1.0 / (dh as f32).sqrt(); let mut o = vec![0f32; t * d]; let mut macs = 0u64;
        for h in 0..heads { for i in 0..t {
            let mut s = vec![0f32; i + 1]; let mut mx = f32::NEG_INFINITY;
            for j in 0..=i { let mut a = 0f32; for c in 0..dh { a += qt.d[i * d + h * dh + c] * kt.d[j * d + h * dh + c]; } s[j] = a * sc; if s[j] > mx { mx = s[j]; } macs += dh as u64; }
            let mut z = 0f32; for j in 0..=i { s[j] = (s[j] - mx).exp(); z += s[j]; }
            for j in 0..=i { let p = s[j] / z; for c in 0..dh { o[i * d + h * dh + c] += p * vt.d[j * d + h * dh + c]; } macs += dh as u64; }
        } }
        self.c().macs += macs; self.c().vec += (heads * t * (t + 1) / 2) as u64 * 3; self.put(out, vec![t, d], o, tile);
    }
    // one query attends over the key and value caches held on the tile (M2 decode)
    fn attnc(&mut self, out: &str, q: &str, kc: &str, vc: &str, heads: usize, tile: usize) {
        let qt = self.fetch(q, tile); let (kt, vt) = (self.get(kc), self.get(vc)); assert_eq!(kt.home, tile); let (t, d) = (kt.dims[0], kt.dims[1]); let dh = d / heads; let sc = 1.0 / (dh as f32).sqrt(); let mut o = vec![0f32; d];
        for h in 0..heads {
            let mut s = vec![0f32; t]; let mut mx = f32::NEG_INFINITY;
            for j in 0..t { let mut a = 0f32; for c in 0..dh { a += qt.d[h * dh + c] * kt.d[j * d + h * dh + c]; } s[j] = a * sc; if s[j] > mx { mx = s[j]; } }
            let mut z = 0f32; for j in 0..t { s[j] = (s[j] - mx).exp(); z += s[j]; }
            for j in 0..t { let p = s[j] / z; for c in 0..dh { o[h * dh + c] += p * vt.d[j * d + h * dh + c]; } }
        }
        let ab = self.ab(); self.c().macs += (2 * d * t) as u64; self.c().rd += (2 * t * d) as u64 * ab; self.c().vec += (heads * t * 3) as u64;
        if self.stripe > 1 && self.stripe_attn {
            // striped attention: the cache is split by head and by context chunk over `stripe` tiles (tile home + i*ltiles); each tile reads its share of the cache and does 1/stripe of the multiply-adds; the query is broadcast and each tile returns one partial (dh values plus the softmax maximum and sum) per head it touches, merged on the home tile
            let sn = self.stripe; let mut maxd = 0u64; for i in 0..sn { maxd = maxd.max(self.sd(tile, i)); }
            let per_macs = ((2 * d * t) as f64 / sn as f64).ceil(); let per_rd = ((2 * t * d) as u64 * ab) as f64 / sn as f64;
            let bc = (d as u64 * ab) / linkbw() + hopcyc() *maxd; let part = (sn.min(heads * 8) * (dh + 2)) as u64 * ab; let ga = part / linkbw() + hopcyc() *maxd;
            self.c().hop += (d as u64 * ab) * maxd + part * maxd;
            self.ovr = Some((per_macs / self.macpc).max(per_rd / self.srambw).ceil() + (bc + ga) as f64 + ((heads * t * 3) as f64 / sn as f64 / VECL).ceil());
        }
        self.put(out, vec![1, d], o, tile);
    }
    fn kvapp(&mut self, cache: &str, newt: &str, tile: usize) {
        let n = self.fetch(newt, tile); let d = *n.dims.last().unwrap(); let ab = self.ab();
        let e = self.t.entry(cache.to_string()).or_insert(Tn { dims: vec![0, d], d: Vec::new(), home: tile }); e.d.extend_from_slice(&n.d); e.dims[0] += n.d.len() / d; self.c().wr += n.d.len() as u64 * ab;
    }
    fn ew(&mut self, out: &str, a: &str, b: Option<&str>, f: &dyn Fn(f32, f32) -> f32) {
        let ta = self.get(a); let tile = ta.home; let tb = b.map(|n| self.fetch(n, tile)); self.c().rd += ta.d.len() as u64 * self.ab();
        let d: Vec<f32> = (0..ta.d.len()).map(|i| f(ta.d[i], tb.as_ref().map_or(0.0, |t| t.d[i]))).collect(); self.c().vec += d.len() as u64; self.put(out, ta.dims.clone(), d, tile);
    }
    fn ln(&mut self, out: &str, a: &str, g: &str, b: &str) {
        let ta = self.get(a); let tile = ta.home; let (gg, bb) = (self.t[g].d.clone(), self.t[b].d.clone()); let n = *ta.dims.last().unwrap(); let mut d = vec![0f32; ta.d.len()]; self.c().rd += ta.d.len() as u64 * self.ab();
        for r in 0..ta.d.len() / n { let x = &ta.d[r * n..(r + 1) * n]; let mu = x.iter().sum::<f32>() / n as f32; let var = x.iter().map(|v| (v - mu) * (v - mu)).sum::<f32>() / n as f32; let is = 1.0 / (var + 1e-5).sqrt(); for j in 0..n { d[r * n + j] = (x[j] - mu) * is * gg[j] + bb[j]; } }
        self.c().vec += d.len() as u64 * 4; self.put(out, ta.dims.clone(), d, tile);
    }
    fn gather(&mut self, out: &str, table: &str, ids: &str, tile: usize) {
        let tb = self.t[table].clone(); let ti = self.fetch(ids, tile); let n = tb.dims[1]; let mut d = Vec::with_capacity(ti.d.len() * n);
        for &i in &ti.d { let r = i as usize; d.extend_from_slice(&tb.d[r * n..(r + 1) * n]); } self.c().rd += d.len() as u64 * self.wb(); self.put(out, vec![ti.d.len(), n], d, tile);
    }
    fn pool2(&mut self, out: &str, a: &str) {
        let t = self.get(a); let (c, h, w) = (t.dims[1], t.dims[2], t.dims[3]); let (oh, ow) = (h / 2, w / 2); let mut d = vec![0f32; c * oh * ow];
        for cc in 0..c { for y in 0..oh { for x in 0..ow { let mut m = f32::NEG_INFINITY; for dy in 0..2 { for dx in 0..2 { m = m.max(t.d[(cc * h + 2 * y + dy) * w + 2 * x + dx]); } } d[(cc * oh + y) * ow + x] = m; } } }
        self.c().rd += t.d.len() as u64 * self.ab(); self.c().vec += t.d.len() as u64; self.put(out, vec![1, c, oh, ow], d, t.home);
    }
}

fn write_counters(sim: &Sim, dir: &str, mode: &str, tiles: usize, side: usize, steps: usize) {
    let mut tags: Vec<&String> = sim.ct.keys().collect(); tags.sort(); let mut tot = Ct::default(); let (mut tcyc, mut ten) = (0f64, 0f64); let mut parts = Vec::new();
    for k in &tags {
        let c = &sim.ct[*k]; tot.macs += c.macs; tot.macs16 += c.macs16; tot.rd += c.rd; tot.wr += c.wr; tot.hop += c.hop; tot.vec += c.vec; tot.net += c.net;
        let cy = *sim.cyc.get(*k).unwrap_or(&0.0); let en = *sim.en.get(*k).unwrap_or(&0.0); tcyc += cy; ten += en;
        parts.push(format!("  \"{}\": {{\"macs\": {}, \"macs_int16_activations\": {}, \"sram_read_bytes\": {}, \"sram_write_bytes\": {}, \"mesh_byte_hops\": {}, \"vector_ops\": {}, \"cycles\": {:.0}, \"dynamic_energy_pj\": {:.1}}}", k, c.macs, c.macs16, c.rd, c.wr, c.hop, c.vec, cy, en));
    }
    let static_pj = tiles as f64 * LEAK_W_PER_GB * (sim.tile_bytes as f64 / 1073741824.0) * (tcyc / CLOCK_HZ) * 1e12;
    let mut f = fs::File::create(format!("{}/counters_{}.json", dir, mode)).unwrap();
    write!(f, "{{\n\"mode\": \"{}\", \"tiles\": {}, \"mesh_side\": {}, \"steps\": {},\n\"total\": {{\"macs\": {}, \"macs_int16_activations\": {}, \"sram_read_bytes\": {}, \"sram_write_bytes\": {}, \"mesh_byte_hops\": {}, \"vector_ops\": {}, \"cycles\": {:.0}, \"dynamic_energy_pj\": {:.1}, \"static_energy_pj\": {:.1}, \"total_energy_pj\": {:.1}}},\n\"per_tag\": {{\n{}\n}}\n}}\n",
           mode, tiles, side, steps, tot.macs, tot.macs16, tot.rd, tot.wr, tot.hop, tot.vec, tcyc, ten, static_pj, ten + static_pj, parts.join(",\n")).unwrap();
}

fn main() {
    let a: Vec<String> = std::env::args().collect(); let dir = &a[1]; let mode = &a[2]; let ns: usize = a[3].parse().unwrap(); let tile_bytes: usize = a.get(4).map_or(4 * 1024 * 1024, |v| v.parse().unwrap()); let decode = a.get(5).map_or(false, |v| v == "decode");
    let int8 = mode == "int8" || mode == "w8"; let a8 = mode == "int8";
    let raw = fs::read(format!("{}/tensors.bin", dir)).unwrap(); let all: Vec<f32> = raw.chunks(4).map(|c| f32::from_le_bytes([c[0], c[1], c[2], c[3]])).collect();
    let mut t = HashMap::new();
    for l in fs::read_to_string(format!("{}/manifest.txt", dir)).unwrap().lines() { let p: Vec<&str> = l.split_whitespace().collect(); let off: usize = p[1].parse().unwrap(); let nd: usize = p[2].parse().unwrap(); let dims: Vec<usize> = p[3..3 + nd].iter().map(|v| v.parse().unwrap()).collect(); let n = numel(&dims); t.insert(p[0].to_string(), Tn { dims, d: all[off..off + n].to_vec(), home: 0 }); }
    let prog: Vec<String> = fs::read_to_string(format!("{}/program.txt", dir)).unwrap().lines().map(|s| s.to_string()).collect();
    let inp = fs::read_to_string(format!("{}/input.txt", dir)).unwrap(); let ip: Vec<&str> = inp.split_whitespace().collect(); let iname = ip[0].to_string(); let idims: Vec<usize> = ip[1..].iter().map(|v| v.parse().unwrap()).collect(); let isz = numel(&idims);
    let iraw = fs::read(format!("{}/inputs.bin", dir)).unwrap(); let idata: Vec<f32> = iraw.chunks(4).map(|c| f32::from_le_bytes([c[0], c[1], c[2], c[3]])).collect();
    let tile_of = |l: &String| -> Option<usize> { let tk: Vec<&str> = l.split_whitespace().collect(); match tk.first().copied() { Some("W") => tk.get(2).and_then(|v| v.parse().ok()), Some("MM") => tk.get(5).and_then(|v| v.parse().ok()), Some("GATHER") => tk.get(4).and_then(|v| v.parse().ok()), Some("ATTN") | Some("ATTNC") => tk.get(6).and_then(|v| v.parse().ok()), Some("KVAPP") => tk.get(3).and_then(|v| v.parse().ok()), Some("CONV") => tk.get(8).and_then(|v| v.parse().ok()), _ => None } };
    let stripe: usize = std::env::var("GPU_STRIPE").ok().and_then(|v| v.parse().ok()).unwrap_or(1); let macpc: f64 = std::env::var("GPU_MACPC").ok().and_then(|v| v.parse().ok()).unwrap_or(MACPC); let srambw: f64 = std::env::var("GPU_SRAMBW").ok().and_then(|v| v.parse().ok()).unwrap_or(SRAMBW);
    let ltiles = prog.iter().filter_map(|l| tile_of(l)).max().unwrap_or(0) + 1; let striped: std::collections::HashSet<String> = prog.iter().filter_map(|l| { let tk: Vec<&str> = l.split_whitespace().collect(); if tk.first() == Some(&"MM") { Some(tk[3].to_string()) } else { None } }).collect(); let tiles = ltiles * stripe.max(1); let side = ((tiles as f64).sqrt().ceil() as usize).max(1);
    let mut sim = Sim { t, wq: HashMap::new(), prec: HashMap::new(), int8, a8, side, tile_bytes, used: HashMap::new(), ct: HashMap::new(), tag: "load".to_string(), cyc: HashMap::new(), en: HashMap::new(), stripe, ltiles, striped, ovr: None, macpc, srambw, stripe_attn: std::env::var("GPU_STRIPE_ATTN").map_or(false, |v| v == "1"), compact: std::env::var("GPU_COMPACT").map_or(false, |v| v == "1") };
    let mut outs: Vec<f32> = Vec::new(); let mut last_out = String::new();
    for s in 0..ns {
        sim.t.insert(iname.clone(), Tn { dims: idims.clone(), d: idata[s * isz..(s + 1) * isz].to_vec(), home: 0 });
        if decode { sim.t.insert("posn".to_string(), Tn { dims: vec![1], d: vec![s as f32], home: 0 }); }
        for line in &prog {
            let mut tok: Vec<&str> = line.split_whitespace().collect(); if tok.is_empty() { continue; }
            if let Some(l) = tok.last() { if l.starts_with('#') { sim.tag = l[1..].to_string(); tok.pop(); } }
            if tok[0] == "W" { sim.tag = "load".to_string(); }
            let before = sim.ct.get(&sim.tag).cloned().unwrap_or_default();
            match tok[0] {
                "W" if sim.stripe > 1 && sim.striped.contains(tok[1]) && sim.t[tok[1]].dims.len() == 2 => { if s > 0 { continue; } let tile: usize = tok[2].parse().unwrap(); let pr = match tok.get(3) { Some(&"a16") => 16u8, Some(&"af") => 0u8, _ => 8u8 };
                    let full = sim.t[tok[1]].clone(); let (k, n) = (full.dims[0], full.dims[1]); let sn = sim.stripe; let per = (n + sn - 1) / sn; sim.prec.insert(tok[1].to_string(), pr); sim.t.get_mut(tok[1]).unwrap().home = tile;
                    for i in 0..sn { let (j0, j1) = (i * per, ((i + 1) * per).min(n)); if j0 >= j1 { continue; } let ni = j1 - j0; let nm = format!("{}#{}", tok[1], i); let ph = sim.stripe_id(tile, i);
                        let mut d = vec![0f32; k * ni]; for kk in 0..k { for j in 0..ni { d[kk * ni + j] = full.d[kk * n + j0 + j]; } }
                        sim.prec.insert(nm.clone(), pr); sim.t.insert(nm.clone(), Tn { dims: vec![k, ni], d: d.clone(), home: ph }); let bytes = d.len() * if int8 { 1 } else { 4 };
                        if int8 { let e = sim.used.entry(ph).or_insert(0); *e += bytes; assert!(*e <= sim.tile_bytes, "tile {} SRAM overflow: {} bytes", ph, *e);
                            let mut sc = vec![0f32; ni]; for j in 0..ni { let mut mx = 0f32; for kk in 0..k { mx = mx.max(d[kk * ni + j].abs()); } sc[j] = if mx > 0.0 { mx / 127.0 } else { 1.0 }; }
                            let q: Vec<i8> = (0..k * ni).map(|x| (d[x] / sc[x % ni]).round().clamp(-127.0, 127.0) as i8).collect(); sim.wq.insert(nm, Wq { q, s: sc, k, n: ni }); }
                        sim.c().wr += bytes as u64; } }
                "W" => { if s > 0 { continue; } let tile: usize = tok[2].parse().unwrap(); let pr = match tok.get(3) { Some(&"a16") => 16u8, Some(&"af") => 0u8, _ => 8u8 }; sim.prec.insert(tok[1].to_string(), pr); let tn = sim.t.get_mut(tok[1]).unwrap(); tn.home = tile; let bytes = tn.d.len() * if int8 { 1 } else { 4 };
                    if int8 { let e = sim.used.entry(tile).or_insert(0); *e += bytes; assert!(*e <= sim.tile_bytes, "tile {} SRAM overflow: {} bytes", tile, *e);
                        let tn = sim.t[tok[1]].clone(); if tn.dims.len() == 2 { let (k, n) = (tn.dims[0], tn.dims[1]); let mut sc = vec![0f32; n]; for j in 0..n { let mut m = 0f32; for kk in 0..k { m = m.max(tn.d[kk * n + j].abs()); } sc[j] = if m > 0.0 { m / 127.0 } else { 1.0 }; }
                            let q: Vec<i8> = (0..k * n).map(|i| (tn.d[i] / sc[i % n]).round().clamp(-127.0, 127.0) as i8).collect(); sim.wq.insert(tok[1].to_string(), Wq { q, s: sc, k, n }); } }
                    sim.c().wr += bytes as u64; }
                "MM" => { sim.mmop(tok[1], tok[2], tok[3], tok[4], tok[5].parse().unwrap()); last_out = tok[1].to_string(); }
                "CONV" => sim.conv(tok[1], tok[2], tok[3], tok[4], tok[5].parse().unwrap(), tok[6].parse().unwrap(), tok[7].parse().unwrap(), tok[8].parse().unwrap()),
                "GATHER" => sim.gather(tok[1], tok[2], tok[3], tok[4].parse().unwrap()),
                "ADD" => sim.ew(tok[1], tok[2], Some(tok[3]), &|x, y| x + y),
                "MUL" => sim.ew(tok[1], tok[2], Some(tok[3]), &|x, y| x * y),
                "RELU" => sim.ew(tok[1], tok[2], None, &|x, _| x.max(0.0)),
                "GELU" => sim.ew(tok[1], tok[2], None, &|x, _| 0.5 * x * (1.0 + (0.7978845608f32 * (x + 0.044715 * x * x * x)).tanh())),
                "LN" => sim.ln(tok[1], tok[2], tok[3], tok[4]),
                "ATTN" => sim.attn(tok[1], tok[2], tok[3], tok[4], tok[5].parse().unwrap(), tok[6].parse().unwrap()),
                "ATTNC" => sim.attnc(tok[1], tok[2], tok[3], tok[4], tok[5].parse().unwrap(), tok[6].parse().unwrap()),
                "KVAPP" => sim.kvapp(tok[1], tok[2], tok[3].parse().unwrap()),
                "MAXPOOL2" => sim.pool2(tok[1], tok[2]),
                "FLATTEN" => { let t = sim.get(tok[2]); let n = t.d.len(); sim.t.insert(tok[1].to_string(), Tn { dims: vec![1, n], d: t.d, home: t.home }); }
                x => panic!("unknown instruction {}", x),
            }
            if tok[0] != "W" { // time and energy of this instruction from its counter changes
                let tg = sim.tag.clone(); let d = sim.ct.get(&tg).cloned().unwrap_or_default().diff(&before); let macs = (d.macs + d.macs16) as f64;
                let cy = match sim.ovr.take() { Some(c) => c + (d.wr as f64 / sim.srambw).ceil() + d.net as f64, None => (macs / sim.macpc).max((d.rd + d.wr) as f64 / sim.srambw).max(d.vec as f64 / VECL).ceil() + d.net as f64 };
                let en = macs * E_MAC_PJ + (d.rd + d.wr) as f64 * E_SRAM_BYTE_PJ + d.vec as f64 * E_VEC_PJ + d.hop as f64 * E_HOP_BYTE_PJ;
                *sim.cyc.entry(tg.clone()).or_insert(0.0) += cy; *sim.en.entry(tg).or_insert(0.0) += en;
            }
        }
        outs.extend_from_slice(&sim.t[&last_out].d);
        if !decode && s == 0 { write_counters(&sim, dir, mode, tiles, side, 1); }
    }
    if decode { write_counters(&sim, dir, mode, tiles, side, ns); }
    let bytes: Vec<u8> = outs.iter().flat_map(|v| v.to_le_bytes()).collect(); fs::write(format!("{}/out_{}.bin", dir, mode), bytes).unwrap();
    eprintln!("ran {} {} in mode {} on {} tiles", ns, if decode { "decode steps" } else { "samples" }, mode, tiles);
}
