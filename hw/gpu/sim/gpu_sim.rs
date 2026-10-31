// Functional simulator of our GPU's tile mesh, milestone M1 (31 Oct 2026). Instruction set: hw/gpu/ISA_M1.md. Standard library only. Build: rustc -O gpu_sim.rs
// usage: gpu_sim DIR MODE NSAMPLES [TILE_BYTES]      MODE = fp32 | int8
// reads DIR/{manifest.txt, tensors.bin, program.txt, inputs.bin, input.txt}; writes DIR/out_MODE.bin (outputs of the last MM, f32) and DIR/counters_MODE.json (counters of sample 0)
use std::collections::HashMap;
use std::fs;
use std::io::Write;

#[derive(Clone)]
struct Tn { dims: Vec<usize>, d: Vec<f32>, home: usize }
struct Wq { q: Vec<i8>, s: Vec<f32>, k: usize, n: usize }
#[derive(Default, Clone)]
struct Ct { macs: u64, rd: u64, wr: u64, hop: u64, vec: u64 }

fn numel(d: &[usize]) -> usize { d.iter().product() }
fn dist(a: usize, b: usize, side: usize) -> u64 { let (ax, ay, bx, by) = ((a % side) as i64, (a / side) as i64, (b % side) as i64, (b / side) as i64); ((ax - bx).abs() + (ay - by).abs()) as u64 }

struct Sim { t: HashMap<String, Tn>, wq: HashMap<String, Wq>, int8: bool, side: usize, tile_bytes: usize, used: HashMap<usize, usize>, ct: HashMap<String, Ct>, tag: String }
impl Sim {
    fn wb(&self) -> u64 { if self.int8 { 1 } else { 4 } }
    fn ab(&self) -> u64 { if self.int8 { 2 } else { 4 } }
    fn c(&mut self) -> &mut Ct { let tag = self.tag.clone(); self.ct.entry(tag).or_default() }
    fn get(&self, n: &str) -> Tn { self.t.get(n).unwrap_or_else(|| panic!("missing tensor {}", n)).clone() }
    fn fetch(&mut self, n: &str, tile: usize) -> Tn { let t = self.get(n); let h = dist(t.home, tile, self.side); let ab = self.ab(); self.c().hop += numel(&t.dims) as u64 * ab * h; self.c().rd += numel(&t.dims) as u64 * ab; t }
    fn put(&mut self, n: &str, dims: Vec<usize>, d: Vec<f32>, home: usize) { let ab = self.ab(); self.c().wr += d.len() as u64 * ab; self.t.insert(n.to_string(), Tn { dims, d, home }); }
    // matrix product a[m,k] @ w[k,n] (+ bias); int8: per-row activation scale, per-column weight scale, int32 accumulate
    fn mm(&mut self, wname: &str, a: &[f32], m: usize, k: usize) -> Vec<f32> {
        let (n, out);
        if self.int8 {
            let w = &self.wq[wname]; assert_eq!(w.k, k); n = w.n; let mut o = vec![0f32; m * n];
            for i in 0..m {
                let row = &a[i * k..(i + 1) * k]; let mx = row.iter().fold(0f32, |x, &v| x.max(v.abs())); let sa = if mx > 0.0 { mx / 127.0 } else { 1.0 };
                let qa: Vec<i32> = row.iter().map(|&v| (v / sa).round().clamp(-127.0, 127.0) as i32).collect(); let mut acc = vec![0i32; n];
                for kk in 0..k { let x = qa[kk]; if x == 0 { continue; } let wr = &w.q[kk * n..(kk + 1) * n]; for j in 0..n { acc[j] += x * wr[j] as i32; } }
                for j in 0..n { o[i * n + j] = acc[j] as f32 * sa * w.s[j]; }
            }
            out = o;
        } else {
            let w = self.t.get(wname).unwrap(); n = w.dims[1]; let mut o = vec![0f32; m * n];
            for i in 0..m { for kk in 0..k { let x = a[i * k + kk]; let wr = &w.d[kk * n..(kk + 1) * n]; for j in 0..n { o[i * n + j] += x * wr[j]; } } }
            out = o;
        }
        let (wbytes, _) = (self.wb(), 0); self.c().macs += (m * k * n) as u64; self.c().rd += (k * n) as u64 * wbytes; out
    }
    fn mmop(&mut self, out: &str, an: &str, wn: &str, bn: &str, tile: usize) {
        assert_eq!(self.t[wn].home, tile, "weight {} is not homed on tile {}", wn, tile);
        let a = self.fetch(an, tile); let k = *self.t[wn].dims.first().unwrap(); let m = a.d.len() / k; let mut o = self.mm(wn, &a.d, m, k); let n = o.len() / m;
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

fn main() {
    let a: Vec<String> = std::env::args().collect(); let dir = &a[1]; let mode = &a[2]; let ns: usize = a[3].parse().unwrap(); let tile_bytes: usize = a.get(4).map_or(4 * 1024 * 1024, |v| v.parse().unwrap()); let int8 = mode == "int8";
    let raw = fs::read(format!("{}/tensors.bin", dir)).unwrap(); let all: Vec<f32> = raw.chunks(4).map(|c| f32::from_le_bytes([c[0], c[1], c[2], c[3]])).collect();
    let mut t = HashMap::new();
    for l in fs::read_to_string(format!("{}/manifest.txt", dir)).unwrap().lines() { let p: Vec<&str> = l.split_whitespace().collect(); let off: usize = p[1].parse().unwrap(); let nd: usize = p[2].parse().unwrap(); let dims: Vec<usize> = p[3..3 + nd].iter().map(|v| v.parse().unwrap()).collect(); let n = numel(&dims); t.insert(p[0].to_string(), Tn { dims, d: all[off..off + n].to_vec(), home: 0 }); }
    let prog: Vec<String> = fs::read_to_string(format!("{}/program.txt", dir)).unwrap().lines().map(|s| s.to_string()).collect();
    let inp = fs::read_to_string(format!("{}/input.txt", dir)).unwrap(); let ip: Vec<&str> = inp.split_whitespace().collect(); let iname = ip[0].to_string(); let idims: Vec<usize> = ip[1..].iter().map(|v| v.parse().unwrap()).collect(); let isz = numel(&idims);
    let iraw = fs::read(format!("{}/inputs.bin", dir)).unwrap(); let idata: Vec<f32> = iraw.chunks(4).map(|c| f32::from_le_bytes([c[0], c[1], c[2], c[3]])).collect();
    let tiles = prog.iter().filter_map(|l| l.split_whitespace().last().and_then(|v| v.parse::<usize>().ok())).max().unwrap_or(0).max(
        prog.iter().filter(|l| l.starts_with("W ")).filter_map(|l| l.split_whitespace().nth(2).and_then(|v| v.parse::<usize>().ok())).max().unwrap_or(0)) + 1;
    let side = (tiles as f64).sqrt().ceil() as usize;
    let mut sim = Sim { t, wq: HashMap::new(), int8, side: side.max(1), tile_bytes, used: HashMap::new(), ct: HashMap::new(), tag: "load".to_string() };
    let mut outs: Vec<f32> = Vec::new(); let mut last_out = String::new();
    for s in 0..ns {
        let pristine: Vec<(String, Tn)> = if s == 0 { Vec::new() } else { Vec::new() }; let _ = pristine;
        // a fresh activation store per sample; weights stay resident after the first sample
        let keep: HashMap<String, Tn> = sim.t.iter().filter(|(k, _)| !sim.ct.is_empty() && sim.wq.contains_key(*k) || false).map(|(k, v)| (k.clone(), v.clone())).collect(); let _ = keep;
        sim.t.insert(iname.clone(), Tn { dims: idims.clone(), d: idata[s * isz..(s + 1) * isz].to_vec(), home: 0 });
        let ctr_before = sim.ct.clone();
        for line in &prog {
            let mut tok: Vec<&str> = line.split_whitespace().collect(); if tok.is_empty() { continue; }
            if let Some(l) = tok.last() { if l.starts_with('#') { sim.tag = l[1..].to_string(); tok.pop(); } }
            match tok[0] {
                "W" => { if s > 0 { continue; } sim.tag = "load".to_string(); let tile: usize = tok[2].parse().unwrap(); let tn = sim.t.get_mut(tok[1]).unwrap(); tn.home = tile; let bytes = tn.d.len() * if int8 { 1 } else { 4 };
                    if int8 { let e = sim.used.entry(tile).or_insert(0); *e += bytes; assert!(*e <= sim.tile_bytes, "tile {} SRAM overflow: {} bytes", tile, *e);
                        let tn = sim.t[tok[1]].clone(); if tn.dims.len() == 2 { let (k, n) = (tn.dims[0], tn.dims[1]); let mut sc = vec![0f32; n]; for j in 0..n { let mut m = 0f32; for kk in 0..k { m = m.max(tn.d[kk * n + j].abs()); } sc[j] = if m > 0.0 { m / 127.0 } else { 1.0 }; }
                            let q: Vec<i8> = (0..k * n).map(|i| (tn.d[i] / sc[i % n]).round().clamp(-127.0, 127.0) as i8).collect(); sim.wq.insert(tok[1].to_string(), Wq { q, s: sc, k, n }); } }
                    let wr = bytes as u64; sim.c().wr += wr; }
                "MM" => { sim.mmop(tok[1], tok[2], tok[3], tok[4], tok[5].parse().unwrap()); last_out = tok[1].to_string(); }
                "CONV" => sim.conv(tok[1], tok[2], tok[3], tok[4], tok[5].parse().unwrap(), tok[6].parse().unwrap(), tok[7].parse().unwrap(), tok[8].parse().unwrap()),
                "GATHER" => sim.gather(tok[1], tok[2], tok[3], tok[4].parse().unwrap()),
                "ADD" => sim.ew(tok[1], tok[2], Some(tok[3]), &|x, y| x + y),
                "MUL" => sim.ew(tok[1], tok[2], Some(tok[3]), &|x, y| x * y),
                "RELU" => sim.ew(tok[1], tok[2], None, &|x, _| x.max(0.0)),
                "GELU" => sim.ew(tok[1], tok[2], None, &|x, _| 0.5 * x * (1.0 + (0.7978845608f32 * (x + 0.044715 * x * x * x)).tanh())),
                "LN" => sim.ln(tok[1], tok[2], tok[3], tok[4]),
                "ATTN" => sim.attn(tok[1], tok[2], tok[3], tok[4], tok[5].parse().unwrap(), tok[6].parse().unwrap()),
                "MAXPOOL2" => sim.pool2(tok[1], tok[2]),
                "FLATTEN" => { let t = sim.get(tok[2]); let n = t.d.len(); sim.t.insert(tok[1].to_string(), Tn { dims: vec![1, n], d: t.d, home: t.home }); }
                x => panic!("unknown instruction {}", x),
            }
        }
        if s == 0 { let _ = ctr_before; }
        let o = &sim.t[&last_out]; outs.extend_from_slice(&o.d);
        if s == 0 { /* counters of sample 0 are final after this sample; later samples add to the totals, so snapshot now */ let snap = sim.ct.clone(); let mut f = fs::File::create(format!("{}/counters_{}.json", dir, mode)).unwrap(); let mut tags: Vec<&String> = snap.keys().collect(); tags.sort();
            let mut tot = Ct::default(); let mut parts = Vec::new();
            for k in &tags { let c = &snap[*k]; tot.macs += c.macs; tot.rd += c.rd; tot.wr += c.wr; tot.hop += c.hop; tot.vec += c.vec; parts.push(format!("  \"{}\": {{\"macs\": {}, \"sram_read_bytes\": {}, \"sram_write_bytes\": {}, \"mesh_byte_hops\": {}, \"vector_ops\": {}}}", k, c.macs, c.rd, c.wr, c.hop, c.vec)); }
            write!(f, "{{\n\"mode\": \"{}\", \"tiles\": {}, \"mesh_side\": {},\n\"total\": {{\"macs\": {}, \"sram_read_bytes\": {}, \"sram_write_bytes\": {}, \"mesh_byte_hops\": {}, \"vector_ops\": {}}},\n\"per_tag\": {{\n{}\n}}\n}}\n", mode, tiles, side, tot.macs, tot.rd, tot.wr, tot.hop, tot.vec, parts.join(",\n")).unwrap(); }
    }
    let bytes: Vec<u8> = outs.iter().flat_map(|v| v.to_le_bytes()).collect(); fs::write(format!("{}/out_{}.bin", dir, mode), bytes).unwrap();
    eprintln!("ran {} samples in mode {} on {} tiles", ns, mode, tiles);
}
