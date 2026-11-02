// Our own inference engine, milestone E1 (2 Nov 2026): fp32 forward pass of a GPT-2-family decoder from a safetensors file. Rust, standard library only. Plan and bars: sw/engine/engine_plan.md
// Build: rustc --edition 2021 -O engine.rs -o engine
// Usage: engine MODEL.safetensors N_HEAD IDS.txt OUT.bin
//   IDS.txt: one prompt per line, token ids separated by spaces. OUT.bin: for each prompt, the logits of every position (f32, little endian), prompts in order.
use std::collections::HashMap;
use std::fs;
use std::io::Write;

// ---- minimal JSON (enough for the safetensors header) ----
#[derive(Debug, Clone)]
enum J { Obj(Vec<(String, J)>), Arr(Vec<J>), Str(String), Num(f64) }
struct P<'a> { s: &'a [u8], i: usize }
impl<'a> P<'a> {
    fn ws(&mut self) { while self.i < self.s.len() && (self.s[self.i] as char).is_whitespace() { self.i += 1; } }
    fn val(&mut self) -> J {
        self.ws();
        match self.s[self.i] {
            b'{' => { self.i += 1; let mut v = Vec::new(); loop { self.ws(); if self.s[self.i] == b'}' { self.i += 1; break; } let k = self.string(); self.ws(); assert_eq!(self.s[self.i], b':'); self.i += 1; let x = self.val(); v.push((k, x)); self.ws(); if self.s[self.i] == b',' { self.i += 1; } } J::Obj(v) }
            b'[' => { self.i += 1; let mut v = Vec::new(); loop { self.ws(); if self.s[self.i] == b']' { self.i += 1; break; } v.push(self.val()); self.ws(); if self.s[self.i] == b',' { self.i += 1; } } J::Arr(v) }
            b'"' => J::Str(self.string()),
            _ => { let st = self.i; while self.i < self.s.len() && !b",]} \n\r\t".contains(&self.s[self.i]) { self.i += 1; } J::Num(std::str::from_utf8(&self.s[st..self.i]).unwrap().parse().unwrap()) }
        }
    }
    fn string(&mut self) -> String { assert_eq!(self.s[self.i], b'"'); self.i += 1; let st = self.i; while self.s[self.i] != b'"' { if self.s[self.i] == b'\\' { self.i += 1; } self.i += 1; } let r = String::from_utf8(self.s[st..self.i].to_vec()).unwrap(); self.i += 1; r }
}

struct T { shape: Vec<usize>, d: Vec<f32> }
fn load(path: &str) -> HashMap<String, T> {
    let raw = fs::read(path).expect("cannot read model file");
    let n = u64::from_le_bytes(raw[0..8].try_into().unwrap()) as usize; let hdr = &raw[8..8 + n]; let base = 8 + n;
    let mut p = P { s: hdr, i: 0 }; let j = p.val(); let mut m = HashMap::new();
    if let J::Obj(items) = j { for (k, v) in items { if k == "__metadata__" { continue; } if let J::Obj(f) = v {
        let get = |name: &str| f.iter().find(|(a, _)| a == name).map(|(_, b)| b.clone()).unwrap();
        let dtype = if let J::Str(s) = get("dtype") { s } else { panic!() }; assert_eq!(dtype, "F32", "this milestone reads fp32 files only (tensor {} is {})", k, dtype);
        let shape: Vec<usize> = if let J::Arr(a) = get("shape") { a.iter().map(|x| if let J::Num(v) = x { *v as usize } else { 0 }).collect() } else { vec![] };
        let (a, b) = if let J::Arr(o) = get("data_offsets") { (if let J::Num(x) = o[0] { x as usize } else { 0 }, if let J::Num(x) = o[1] { x as usize } else { 0 }) } else { (0, 0) };
        let d: Vec<f32> = raw[base + a..base + b].chunks_exact(4).map(|c| f32::from_le_bytes([c[0], c[1], c[2], c[3]])).collect();
        m.insert(k, T { shape, d }); } } }
    m
}

fn layer_norm(x: &[f32], t: usize, n: usize, g: &[f32], b: &[f32]) -> Vec<f32> {
    let mut o = vec![0f32; t * n];
    for r in 0..t { let row = &x[r * n..(r + 1) * n]; let mu = row.iter().sum::<f32>() / n as f32; let var = row.iter().map(|v| (v - mu) * (v - mu)).sum::<f32>() / n as f32; let is = 1.0 / (var + 1e-5).sqrt(); for j in 0..n { o[r * n + j] = (row[j] - mu) * is * g[j] + b[j]; } }
    o
}
// y[t,m] = x[t,k] @ w[k,m] + b[m]   (GPT-2's Conv1D layout: w is [in, out])
fn linear(x: &[f32], t: usize, k: usize, w: &[f32], m: usize, b: &[f32]) -> Vec<f32> {
    let mut y = vec![0f32; t * m];
    for r in 0..t { let yr = &mut y[r * m..(r + 1) * m]; yr.copy_from_slice(b); for kk in 0..k { let xv = x[r * k + kk]; let wr = &w[kk * m..(kk + 1) * m]; for j in 0..m { yr[j] += xv * wr[j]; } } }
    y
}
fn gelu_new(x: f32) -> f32 { 0.5 * x * (1.0 + (0.7978845608028654f32 * (x + 0.044715 * x * x * x)).tanh()) }

fn forward(m: &HashMap<String, T>, nl: usize, nh: usize, ids: &[usize]) -> Vec<f32> {
    let g = |k: &str| &m.get(k).unwrap_or_else(|| panic!("missing tensor {}", k)).d[..];
    let wte = m.get("transformer.wte.weight").unwrap(); let (vocab, n) = (wte.shape[0], wte.shape[1]); let wpe = g("transformer.wpe.weight"); let t = ids.len(); let dh = n / nh;
    let mut x = vec![0f32; t * n];
    for (i, &id) in ids.iter().enumerate() { for j in 0..n { x[i * n + j] = wte.d[id * n + j] + wpe[i * n + j]; } }
    for l in 0..nl {
        let p = |s: &str| format!("transformer.h.{}.{}", l, s);
        let h = layer_norm(&x, t, n, g(&p("ln_1.weight")), g(&p("ln_1.bias")));
        let qkv = linear(&h, t, n, g(&p("attn.c_attn.weight")), 3 * n, g(&p("attn.c_attn.bias")));
        let mut a = vec![0f32; t * n]; let sc = 1.0 / (dh as f32).sqrt();
        for hd in 0..nh { for i in 0..t {
            let mut s = vec![0f32; i + 1]; let mut mx = f32::NEG_INFINITY;
            for j in 0..=i { let mut d = 0f32; for c in 0..dh { d += qkv[i * 3 * n + hd * dh + c] * qkv[j * 3 * n + n + hd * dh + c]; } s[j] = d * sc; if s[j] > mx { mx = s[j]; } }
            let mut z = 0f32; for j in 0..=i { s[j] = (s[j] - mx).exp(); z += s[j]; }
            for j in 0..=i { let pj = s[j] / z; for c in 0..dh { a[i * n + hd * dh + c] += pj * qkv[j * 3 * n + 2 * n + hd * dh + c]; } }
        } }
        let o = linear(&a, t, n, g(&p("attn.c_proj.weight")), n, g(&p("attn.c_proj.bias"))); for i in 0..t * n { x[i] += o[i]; }
        let h2 = layer_norm(&x, t, n, g(&p("ln_2.weight")), g(&p("ln_2.bias")));
        let mut u = linear(&h2, t, n, g(&p("mlp.c_fc.weight")), 4 * n, g(&p("mlp.c_fc.bias"))); for v in u.iter_mut() { *v = gelu_new(*v); }
        let dn = linear(&u, t, 4 * n, g(&p("mlp.c_proj.weight")), n, g(&p("mlp.c_proj.bias"))); for i in 0..t * n { x[i] += dn[i]; }
    }
    let xf = layer_norm(&x, t, n, g("transformer.ln_f.weight"), g("transformer.ln_f.bias"));
    let mut logits = vec![0f32; t * vocab];
    for i in 0..t { let xr = &xf[i * n..(i + 1) * n]; for v in 0..vocab { let w = &wte.d[v * n..(v + 1) * n]; let mut d = 0f32; for j in 0..n { d += xr[j] * w[j]; } logits[i * vocab + v] = d; } }
    logits
}

// ---- E4: incremental decoding with a key-value cache. One token per call: computes this position's keys and values, appends them, attends over the cache, returns this position's logits.
struct Cache { k: Vec<Vec<f32>>, v: Vec<Vec<f32>>, len: usize }
impl Cache { fn new(nl: usize) -> Cache { Cache { k: vec![Vec::new(); nl], v: vec![Vec::new(); nl], len: 0 } } }
fn step(m: &HashMap<String, T>, nl: usize, nh: usize, c: &mut Cache, id: usize) -> Vec<f32> {
    let g = |k: &str| &m.get(k).unwrap_or_else(|| panic!("missing tensor {}", k)).d[..];
    let wte = m.get("transformer.wte.weight").unwrap(); let (vocab, n) = (wte.shape[0], wte.shape[1]); let wpe = g("transformer.wpe.weight"); let pos = c.len; let dh = n / nh;
    let mut x = vec![0f32; n]; for j in 0..n { x[j] = wte.d[id * n + j] + wpe[pos * n + j]; }
    for l in 0..nl {
        let p = |s: &str| format!("transformer.h.{}.{}", l, s);
        let h = layer_norm(&x, 1, n, g(&p("ln_1.weight")), g(&p("ln_1.bias")));
        let qkv = linear(&h, 1, n, g(&p("attn.c_attn.weight")), 3 * n, g(&p("attn.c_attn.bias")));
        c.k[l].extend_from_slice(&qkv[n..2 * n]); c.v[l].extend_from_slice(&qkv[2 * n..3 * n]); let t = pos + 1;
        let mut a = vec![0f32; n]; let sc = 1.0 / (dh as f32).sqrt();
        for hd in 0..nh {
            let mut s = vec![0f32; t]; let mut mx = f32::NEG_INFINITY;
            for j in 0..t { let mut d = 0f32; for cc in 0..dh { d += qkv[hd * dh + cc] * c.k[l][j * n + hd * dh + cc]; } s[j] = d * sc; if s[j] > mx { mx = s[j]; } }
            let mut z = 0f32; for j in 0..t { s[j] = (s[j] - mx).exp(); z += s[j]; }
            for j in 0..t { let pj = s[j] / z; for cc in 0..dh { a[hd * dh + cc] += pj * c.v[l][j * n + hd * dh + cc]; } }
        }
        let o = linear(&a, 1, n, g(&p("attn.c_proj.weight")), n, g(&p("attn.c_proj.bias"))); for i in 0..n { x[i] += o[i]; }
        let h2 = layer_norm(&x, 1, n, g(&p("ln_2.weight")), g(&p("ln_2.bias")));
        let mut u = linear(&h2, 1, n, g(&p("mlp.c_fc.weight")), 4 * n, g(&p("mlp.c_fc.bias"))); for v in u.iter_mut() { *v = gelu_new(*v); }
        let dn = linear(&u, 1, 4 * n, g(&p("mlp.c_proj.weight")), n, g(&p("mlp.c_proj.bias"))); for i in 0..n { x[i] += dn[i]; }
    }
    c.len += 1;
    let xf = layer_norm(&x, 1, n, g("transformer.ln_f.weight"), g("transformer.ln_f.bias")); let mut logits = vec![0f32; vocab];
    for v in 0..vocab { let w = &wte.d[v * n..(v + 1) * n]; let mut d = 0f32; for j in 0..n { d += xf[j] * w[j]; } logits[v] = d; }
    logits
}

// ---- E2: INT8 weights (weight-only). Layer matrices ([in, out]) get one scale per output column; the tied output embedding ([vocab, n]) one scale per row. Activations, biases, layer norms and position embeddings stay fp32.
struct QW { q: Vec<i8>, s: Vec<f32> }
fn quant_cols(w: &[f32], k: usize, m: usize) -> QW {
    let mut s = vec![0f32; m]; for kk in 0..k { for j in 0..m { let a = w[kk * m + j].abs(); if a > s[j] { s[j] = a; } } } for v in s.iter_mut() { *v = if *v > 0.0 { *v / 127.0 } else { 1.0 }; }
    let q = (0..k * m).map(|i| (w[i] / s[i % m]).round().clamp(-127.0, 127.0) as i8).collect(); QW { q, s }
}
fn quant_rows(w: &[f32], rows: usize, n: usize) -> QW {
    let mut s = vec![0f32; rows]; for r in 0..rows { let mx = w[r * n..(r + 1) * n].iter().fold(0f32, |a, &v| a.max(v.abs())); s[r] = if mx > 0.0 { mx / 127.0 } else { 1.0 }; }
    let q = (0..rows * n).map(|i| (w[i] / s[i / n]).round().clamp(-127.0, 127.0) as i8).collect(); QW { q, s }
}
fn linear_q(x: &[f32], k: usize, w: &QW, m: usize, b: &[f32]) -> Vec<f32> {
    let mut acc = vec![0f32; m]; for kk in 0..k { let xv = x[kk]; let row = &w.q[kk * m..(kk + 1) * m]; for j in 0..m { acc[j] += xv * row[j] as f32; } }
    for j in 0..m { acc[j] = b[j] + acc[j] * w.s[j]; } acc
}
struct QModel { wte: QW, l: Vec<[QW; 4]> } // per layer: c_attn, attn c_proj, c_fc, mlp c_proj
fn build_q(m: &HashMap<String, T>, nl: usize) -> QModel {
    let wte = m.get("transformer.wte.weight").unwrap(); let n = wte.shape[1];
    let mut l = Vec::new();
    for i in 0..nl { let f = |s: &str| { let t = m.get(&format!("transformer.h.{}.{}", i, s)).unwrap(); quant_cols(&t.d, t.shape[0], t.shape[1]) }; l.push([f("attn.c_attn.weight"), f("attn.c_proj.weight"), f("mlp.c_fc.weight"), f("mlp.c_proj.weight")]); }
    QModel { wte: quant_rows(&wte.d, wte.shape[0], n), l }
}
fn step_q(m: &HashMap<String, T>, qm: &QModel, nh: usize, c: &mut Cache, id: usize) -> Vec<f32> {
    let nl = qm.l.len(); let g = |k: &str| &m.get(k).unwrap_or_else(|| panic!("missing tensor {}", k)).d[..];
    let wte = m.get("transformer.wte.weight").unwrap(); let (vocab, n) = (wte.shape[0], wte.shape[1]); let wpe = g("transformer.wpe.weight"); let pos = c.len; let dh = n / nh;
    let mut x = vec![0f32; n]; for j in 0..n { x[j] = qm.wte.q[id * n + j] as f32 * qm.wte.s[id] + wpe[pos * n + j]; }
    for l in 0..nl {
        let p = |s: &str| format!("transformer.h.{}.{}", l, s); let w = &qm.l[l];
        let h = layer_norm(&x, 1, n, g(&p("ln_1.weight")), g(&p("ln_1.bias")));
        let qkv = linear_q(&h, n, &w[0], 3 * n, g(&p("attn.c_attn.bias")));
        c.k[l].extend_from_slice(&qkv[n..2 * n]); c.v[l].extend_from_slice(&qkv[2 * n..3 * n]); let t = pos + 1;
        let mut a = vec![0f32; n]; let sc = 1.0 / (dh as f32).sqrt();
        for hd in 0..nh {
            let mut s = vec![0f32; t]; let mut mx = f32::NEG_INFINITY;
            for j in 0..t { let mut d = 0f32; for cc in 0..dh { d += qkv[hd * dh + cc] * c.k[l][j * n + hd * dh + cc]; } s[j] = d * sc; if s[j] > mx { mx = s[j]; } }
            let mut z = 0f32; for j in 0..t { s[j] = (s[j] - mx).exp(); z += s[j]; }
            for j in 0..t { let pj = s[j] / z; for cc in 0..dh { a[hd * dh + cc] += pj * c.v[l][j * n + hd * dh + cc]; } }
        }
        let o = linear_q(&a, n, &w[1], n, g(&p("attn.c_proj.bias"))); for i in 0..n { x[i] += o[i]; }
        let h2 = layer_norm(&x, 1, n, g(&p("ln_2.weight")), g(&p("ln_2.bias")));
        let mut u = linear_q(&h2, n, &w[2], 4 * n, g(&p("mlp.c_fc.bias"))); for v in u.iter_mut() { *v = gelu_new(*v); }
        let dn = linear_q(&u, 4 * n, &w[3], n, g(&p("mlp.c_proj.bias"))); for i in 0..n { x[i] += dn[i]; }
    }
    c.len += 1;
    let xf = layer_norm(&x, 1, n, g("transformer.ln_f.weight"), g("transformer.ln_f.bias")); let mut logits = vec![0f32; vocab];
    for v in 0..vocab { let w = &qm.wte.q[v * n..(v + 1) * n]; let mut d = 0f32; for j in 0..n { d += xf[j] * w[j] as f32; } logits[v] = d * qm.wte.s[v]; }
    logits
}
fn nll(logits: &[f32], target: usize) -> f64 { let mx = logits.iter().cloned().fold(f32::NEG_INFINITY, f32::max); let z: f64 = logits.iter().map(|&v| ((v - mx) as f64).exp()).sum(); (z.ln() + mx as f64) - logits[target] as f64 }

fn main() {
    let a: Vec<String> = std::env::args().collect(); if a.len() < 5 { eprintln!("usage: engine MODEL.safetensors N_HEAD IDS.txt OUT [decode|decode_q|loss|loss_q]"); std::process::exit(2); }
    if a.len() > 5 && (a[5] == "loss" || a[5] == "loss_q" || a[5] == "decode_q") {
        // E2: loss = mean next-token loss per window (one line per window in OUT); loss_q uses INT8 weights; decode_q prints time per token by position window with INT8 weights; sizes are reported on stderr
        let m = load(&a[1]); let nh: usize = a[2].parse().unwrap(); let mut nl = 0; while m.contains_key(&format!("transformer.h.{}.ln_1.weight", nl)) { nl += 1; }
        let q = a[5] != "loss"; let qm = if q { Some(build_q(&m, nl)) } else { None };
        let fp32: usize = (0..nl).map(|i| ["attn.c_attn.weight", "attn.c_proj.weight", "mlp.c_fc.weight", "mlp.c_proj.weight"].iter().map(|s| m[&format!("transformer.h.{}.{}", i, s)].d.len() * 4).sum::<usize>()).sum::<usize>() + m["transformer.wte.weight"].d.len() * 4;
        if let Some(qm) = &qm { let int8: usize = qm.l.iter().map(|w| w.iter().map(|x| x.q.len() + x.s.len() * 4).sum::<usize>()).sum::<usize>() + qm.wte.q.len() + qm.wte.s.len() * 4; eprintln!("weights read per token: fp32 {:.1} MB, INT8 {:.1} MB, ratio {:.3}", fp32 as f64 / 1e6, int8 as f64 / 1e6, int8 as f64 / fp32 as f64); }
        let prompts: Vec<Vec<usize>> = fs::read_to_string(&a[3]).unwrap().lines().filter(|l| !l.trim().is_empty()).map(|l| l.split_whitespace().map(|v| v.parse().unwrap()).collect()).collect();
        let mut out = fs::File::create(&a[4]).unwrap(); let win = 64usize; let mut tw: Vec<(f64, usize)> = Vec::new(); let t0 = std::time::Instant::now();
        for p in &prompts { let mut c = Cache::new(nl); let mut tot = 0f64;
            for (i, &id) in p.iter().enumerate() {
                let ts = std::time::Instant::now(); let lg = if q { step_q(&m, qm.as_ref().unwrap(), nh, &mut c, id) } else { step(&m, nl, nh, &mut c, id) }; let dt = ts.elapsed().as_secs_f64();
                if a[5] == "decode_q" && p.len() >= 256 { let w = i / win; if tw.len() <= w { tw.resize(w + 1, (0.0, 0)); } tw[w].0 += dt; tw[w].1 += 1; }
                if i + 1 < p.len() { tot += nll(&lg, p[i + 1]); } }
            writeln!(out, "{:.6}", tot / (p.len() - 1) as f64).unwrap(); }
        for (w, (s, n)) in tw.iter().enumerate() { if *n > 0 { eprintln!("positions {:>4}..{:>4}: {:.2} ms per token", w * win, (w + 1) * win - 1, s / *n as f64 * 1e3); } }
        eprintln!("{} windows in {:.1} s", prompts.len(), t0.elapsed().as_secs_f64()); return;
    }
    if a.len() > 5 && a[5] == "decode" {
        // E4: one token at a time with the cache; writes the logits of every position (same format as the full pass) and prints the time per token by position window
        let m = load(&a[1]); let nh: usize = a[2].parse().unwrap(); let mut nl = 0; while m.contains_key(&format!("transformer.h.{}.ln_1.weight", nl)) { nl += 1; }
        let prompts: Vec<Vec<usize>> = fs::read_to_string(&a[3]).unwrap().lines().filter(|l| !l.trim().is_empty()).map(|l| l.split_whitespace().map(|v| v.parse().unwrap()).collect()).collect();
        let mut out = fs::File::create(&a[4]).unwrap(); let win = 64usize; let mut tw: Vec<(f64, usize)> = Vec::new();
        for p in &prompts { let mut c = Cache::new(nl); for (i, &id) in p.iter().enumerate() {
            let t0 = std::time::Instant::now(); let lg = step(&m, nl, nh, &mut c, id); let dt = t0.elapsed().as_secs_f64();
            if p.len() >= 256 { let w = i / win; if tw.len() <= w { tw.resize(w + 1, (0.0, 0)); } tw[w].0 += dt; tw[w].1 += 1; }
            let bytes: Vec<u8> = lg.iter().flat_map(|v| v.to_le_bytes()).collect(); out.write_all(&bytes).unwrap(); } }
        for (w, (s, n)) in tw.iter().enumerate() { if *n > 0 { eprintln!("positions {:>4}..{:>4}: {:.2} ms per token", w * win, (w + 1) * win - 1, s / *n as f64 * 1e3); } }
        return;
    }
    let m = load(&a[1]); let nh: usize = a[2].parse().unwrap(); let mut nl = 0; while m.contains_key(&format!("transformer.h.{}.ln_1.weight", nl)) { nl += 1; }
    let prompts: Vec<Vec<usize>> = fs::read_to_string(&a[3]).unwrap().lines().filter(|l| !l.trim().is_empty()).map(|l| l.split_whitespace().map(|v| v.parse().unwrap()).collect()).collect();
    let mut out = fs::File::create(&a[4]).unwrap(); let t0 = std::time::Instant::now();
    for p in &prompts { let lg = forward(&m, nl, nh, p); let bytes: Vec<u8> = lg.iter().flat_map(|v| v.to_le_bytes()).collect(); out.write_all(&bytes).unwrap(); }
    eprintln!("{} layers, {} heads, {} prompts, {:.2} s", nl, nh, prompts.len(), t0.elapsed().as_secs_f64());
}
