// L Compute IR optimiser (step 3b). Passes, in order: (1) full unrolling of short constant-trip-count straight-line loops, (2) one forward pass inside each straight-line region that folds constants, turns "register + constant" into AddImm and removes repeated pure computations (value numbering), (3) fuse "compute into a temporary, then Mov" into one instruction, (4) remove pure instructions whose result is never read.
// The optimised kernel must compute exactly the same values as the original (bar C1 compares them bit for bit). Loads, stores, barriers, integer division and anything with a possible error are never removed or merged, so errors are still reported.
use crate::ir::*;
use std::collections::HashMap;

fn dst(i: &Inst) -> Option<Reg> { use Inst::*; match i {
    ConstI(d, _) | ConstF(d, _) | Special(d, _) | ParamS(d, _) | Mov(d, _) | AddImm(d, _, _) | BinI(d, _, _, _) | BinF(d, _, _, _) | CmpI(d, _, _, _) | CmpF(d, _, _, _)
    | UnF(d, _, _) | CvtIF(d, _) | CvtFI(d, _) | SelF(d, _, _, _) | LdG(d, _, _) | LdS(d, _, _) => Some(*d), _ => None } }
fn set_dst(i: &mut Inst, n: Reg) { use Inst::*; match i {
    ConstI(d, _) | ConstF(d, _) | Special(d, _) | ParamS(d, _) | Mov(d, _) | AddImm(d, _, _) | BinI(d, _, _, _) | BinF(d, _, _, _) | CmpI(d, _, _, _) | CmpF(d, _, _, _)
    | UnF(d, _, _) | CvtIF(d, _) | CvtFI(d, _) | SelF(d, _, _, _) | LdG(d, _, _) | LdS(d, _, _) => *d = n, _ => {} } }
fn srcs(i: &Inst) -> Vec<Reg> { use Inst::*; match i {
    Mov(_, a) | AddImm(_, a, _) | UnF(_, _, a) | CvtIF(_, a) | CvtFI(_, a) | LdG(_, _, a) | LdS(_, _, a) | BrIf(a, _) | BrIfNot(a, _) => vec![*a],
    BinI(_, _, a, b) | BinF(_, _, a, b) | CmpI(_, _, a, b) | CmpF(_, _, a, b) | StG(_, a, b) | StS(_, a, b) => vec![*a, *b],
    SelF(_, p, a, b) => vec![*p, *a, *b], _ => vec![] } }
// can be dropped when its result is unused / merged with an identical earlier one
fn pure(i: &Inst) -> bool { use Inst::*; match i { LdG(..) | LdS(..) => false, BinI(_, BinOp::Div, _, _) | BinI(_, BinOp::Rem, _, _) => false, _ => dst(i).is_some() } }
fn straight(i: &Inst) -> bool { !matches!(i, Inst::Label(_) | Inst::Br(_) | Inst::BrIf(..) | Inst::BrIfNot(..) | Inst::Ret) }

// ---------- pass 1: unrolling ----------
fn unroll_one(code: &[Inst], nregs: usize) -> Option<Vec<Inst>> {
    let mut writes = vec![0u32; nregs]; let mut cval: Vec<Option<i32>> = vec![None; nregs];
    for ins in code { if let Some(d) = dst(ins) { writes[d.0 as usize] += 1; if let Inst::ConstI(_, v) = ins { cval[d.0 as usize] = Some(*v); } } }
    let konst = |r: Reg| if writes[r.0 as usize] == 1 { cval[r.0 as usize] } else { None };
    let refs = |l: u32| code.iter().filter(|x| matches!(x, Inst::Br(m) | Inst::BrIf(_, m) | Inst::BrIfNot(_, m) if *m == l)).count();
    for l in 0..code.len() {
        let top = match code[l] { Inst::Label(t) => t, _ => continue };
        if l + 2 >= code.len() { continue; }
        let (i, end, p) = match (&code[l + 1], &code[l + 2]) { (Inst::CmpI(p, CmpOp::Lt, i, e), Inst::BrIfNot(p2, _)) if p == p2 => (*i, *e, *p), _ => continue };
        let out = match code[l + 2] { Inst::BrIfNot(_, o) => o, _ => continue };
        let b = match (l + 3..code.len()).find(|&j| matches!(code[j], Inst::Br(t) if t == top)) { Some(b) => b, None => continue };
        if b + 1 >= code.len() || !matches!(code[b + 1], Inst::Label(o) if o == out) { continue; }
        let st = match code[b - 1] { Inst::BinI(a, BinOp::Add, c, s) if a == i && c == i => s, _ => continue };
        let body = &code[l + 3..b - 1];
        if !body.iter().all(straight) || body.iter().any(|x| dst(x) == Some(i) || dst(x) == Some(p)) || refs(top) != 1 || refs(out) != 1 || writes[i.0 as usize] != 2 { continue; }
        let m = match (0..l).rev().find(|&j| dst(&code[j]) == Some(i)) { Some(m) => m, None => continue };
        let s = match code[m] { Inst::Mov(_, s) => s, _ => continue };
        if !code[m + 1..l].iter().all(straight) { continue; }
        let (start, e, step) = match (konst(s), konst(end), konst(st)) { (Some(a), Some(b2), Some(c)) if c > 0 => (a, b2, c), _ => continue };
        let trips = (if e > start { ((e - start) + step - 1) / step } else { 0 }) as usize;
        if trips > 64 || trips * (body.len() + 1) > 700 { continue; }
        let mut out_code: Vec<Inst> = code[..l].to_vec(); let mut v = start;
        for _ in 0..trips { out_code.push(Inst::ConstI(i, v)); out_code.extend(body.iter().cloned()); v += step; }
        out_code.push(Inst::ConstI(i, v)); // the value the loop variable has after the loop
        out_code.extend(code[b + 2..].iter().cloned()); return Some(out_code);
    }
    None
}

// ---------- pass 2: constants and repeated computations inside straight-line regions ----------
type Key = (u32, u32, u32, u32, u32, u32, u32);
fn fold_int(op: BinOp, x: i32, y: i32) -> Option<i32> { Some(match op { BinOp::Add => x.wrapping_add(y), BinOp::Sub => x.wrapping_sub(y), BinOp::Mul => x.wrapping_mul(y), BinOp::Min => x.min(y), BinOp::Max => x.max(y),
    BinOp::And => x & y, BinOp::Or => x | y, BinOp::Shl => x << (y & 31), BinOp::Shr => x >> (y & 31), BinOp::Div => { if y == 0 { return None; } x / y } BinOp::Rem => { if y == 0 { return None; } x % y } }) }
fn fold_cmp(op: CmpOp, x: i32, y: i32) -> i32 { (match op { CmpOp::Lt => x < y, CmpOp::Le => x <= y, CmpOp::Gt => x > y, CmpOp::Ge => x >= y, CmpOp::Eq => x == y, CmpOp::Ne => x != y }) as i32 }
fn opn(o: BinOp) -> u32 { o as u32 } fn cmpn(o: CmpOp) -> u32 { o as u32 } fn unn(o: UnOp) -> u32 { o as u32 }

fn fold(code: &[Inst], nregs: usize) -> Vec<Inst> {
    let mut ver = vec![1u32; nregs]; let mut kc: Vec<Option<(u32, u32)>> = vec![None; nregs]; let mut table: HashMap<Key, (Reg, u32)> = HashMap::new(); let mut out: Vec<Inst> = Vec::with_capacity(code.len());
    macro_rules! cv { ($r:expr) => { match kc[$r.0 as usize] { Some((v, vv)) if vv == ver[$r.0 as usize] => Some(v), _ => None } } }
    macro_rules! write { ($d:expr) => { ver[$d.0 as usize] += 1; kc[$d.0 as usize] = None; } }
    macro_rules! emit_const { ($d:expr, $bits:expr) => { { let (d, bits): (Reg, u32) = ($d, $bits); if cv!(d) == Some(bits) {} else { out.push(Inst::ConstI(d, bits as i32)); write!(d); kc[d.0 as usize] = Some((bits, ver[d.0 as usize])); } } } }
    // emit `ins` (which writes d) unless an identical computation (same operands, same versions) is still held in some register
    macro_rules! emit_expr { ($d:expr, $key:expr, $ins:expr) => { { let (d, key): (Reg, Key) = ($d, $key);
        match table.get(&key).copied() { Some((r, v)) if ver[r.0 as usize] == v => { if r != d { out.push(Inst::Mov(d, r)); let c = cv!(r); write!(d); if let Some(c) = c { kc[d.0 as usize] = Some((c, ver[d.0 as usize])); } } }
            _ => { out.push($ins); write!(d); table.insert(key, (d, ver[d.0 as usize])); } } } } }
    let v = |ver: &Vec<u32>, r: Reg| ver[r.0 as usize];
    for ins in code {
        match ins {
            Inst::Label(_) => { table.clear(); for c in kc.iter_mut() { *c = None; } out.push(ins.clone()); }
            Inst::ConstI(d, x) => emit_const!(*d, *x as u32), Inst::ConstF(d, x) => emit_const!(*d, x.to_bits()),
            Inst::Mov(d, s) => { if d == s { continue; } match cv!(*s) { Some(c) => emit_const!(*d, c), None => { out.push(ins.clone()); write!(*d); } } }
            Inst::BinI(d, op, a, b) => {
                let (ca, cb) = (cv!(*a), cv!(*b));
                if let (Some(x), Some(y)) = (ca, cb) { if let Some(r) = fold_int(*op, x as i32, y as i32) { emit_const!(*d, r as u32); continue; } }
                let imm = match (op, ca, cb) { (BinOp::Add, _, Some(y)) => Some((*a, y as i32)), (BinOp::Add, Some(x), _) => Some((*b, x as i32)), (BinOp::Sub, _, Some(y)) => Some((*a, (y as i32).wrapping_neg())), _ => None };
                if let Some((s, c)) = imm { if c == 0 { if s != *d { out.push(Inst::Mov(*d, s)); write!(*d); } continue; }
                    emit_expr!(*d, (1, v(&ver, s), s.0, c as u32, 0, 0, 0), Inst::AddImm(*d, s, c)); continue; }
                if pure(ins) { emit_expr!(*d, (2, opn(*op), a.0, v(&ver, *a), b.0, v(&ver, *b), 0), ins.clone()); } else { out.push(ins.clone()); write!(*d); }
            }
            Inst::BinF(d, op, a, b) => emit_expr!(*d, (3, opn(*op), a.0, v(&ver, *a), b.0, v(&ver, *b), 0), ins.clone()),
            Inst::CmpI(d, op, a, b) => { if let (Some(x), Some(y)) = (cv!(*a), cv!(*b)) { emit_const!(*d, fold_cmp(*op, x as i32, y as i32) as u32); continue; }
                emit_expr!(*d, (4, cmpn(*op), a.0, v(&ver, *a), b.0, v(&ver, *b), 0), ins.clone()) }
            Inst::CmpF(d, op, a, b) => emit_expr!(*d, (5, cmpn(*op), a.0, v(&ver, *a), b.0, v(&ver, *b), 0), ins.clone()),
            Inst::UnF(d, op, a) => emit_expr!(*d, (6, unn(*op), a.0, v(&ver, *a), 0, 0, 0), ins.clone()),
            Inst::CvtIF(d, a) => emit_expr!(*d, (7, 0, a.0, v(&ver, *a), 0, 0, 0), ins.clone()), Inst::CvtFI(d, a) => emit_expr!(*d, (8, 0, a.0, v(&ver, *a), 0, 0, 0), ins.clone()),
            Inst::SelF(d, p, a, b) => emit_expr!(*d, (9, p.0, v(&ver, *p), a.0, v(&ver, *a), b.0, v(&ver, *b)), ins.clone()),
            Inst::Special(d, s) => { let (t, ax) = match s { Sp::Tid(a) => (0, *a), Sp::Bid(a) => (1, *a), Sp::Bdim(a) => (2, *a), Sp::Gdim(a) => (3, *a) }; emit_expr!(*d, (10, t, ax as u32, 0, 0, 0, 0), ins.clone()) }
            Inst::ParamS(d, p) => emit_expr!(*d, (11, *p, 0, 0, 0, 0, 0), ins.clone()),
            Inst::AddImm(d, s, c) => emit_expr!(*d, (1, v(&ver, *s), s.0, *c as u32, 0, 0, 0), ins.clone()),
            _ => { out.push(ins.clone()); if let Some(d) = dst(ins) { write!(d); } }
        }
    }
    out
}

// ---------- pass 3: temporary + Mov fusion ----------
fn fuse(code: &mut Vec<Inst>, nregs: usize) {
    let mut reads = vec![0u32; nregs]; for ins in code.iter() { for r in srcs(ins) { reads[r.0 as usize] += 1; } }
    let mut pairs: Vec<usize> = Vec::new(); let mut adj = vec![0u32; nregs];
    for j in 1..code.len() { if let Inst::Mov(d, t) = code[j] { if d != t && dst(&code[j - 1]) == Some(t) && !matches!(code[j - 1], Inst::Mov(..)) { pairs.push(j); adj[t.0 as usize] += 1; } } }
    let mut remove = vec![false; code.len()];
    for &j in &pairs { if let Inst::Mov(d, t) = code[j] { if reads[t.0 as usize] == adj[t.0 as usize] { set_dst(&mut code[j - 1], d); remove[j] = true; } } }
    let mut k = 0; code.retain(|_| { k += 1; !remove[k - 1] });
}

// ---------- pass 4: dead code ----------
fn dce(code: &mut Vec<Inst>, nregs: usize) {
    loop {
        let mut reads = vec![0u32; nregs]; for ins in code.iter() { for r in srcs(ins) { reads[r.0 as usize] += 1; } }
        let before = code.len(); code.retain(|ins| !(pure(ins) && reads[dst(ins).unwrap().0 as usize] == 0)); if code.len() == before { break; }
    }
}

pub fn optimise(k: &Kernel) -> Kernel {
    let n = k.regs.len(); let mut code = k.code.clone();
    for _ in 0..8 { match unroll_one(&code, n) { Some(c) => code = c, None => break } }
    code = fold(&code, n); dce(&mut code, n); fuse(&mut code, n); dce(&mut code, n);
    Kernel { name: k.name.clone(), params: k.params.clone(), shared: k.shared.clone(), regs: k.regs.clone(), code }
}

// registers actually used by the code (the fast back end allocates one row of lanes per register, so unused rows cost cache space)
pub fn used_regs(k: &Kernel) -> usize { let mut u = std::collections::HashSet::new(); for i in &k.code { if let Some(d) = dst(i) { u.insert(d.0); } for r in srcs(i) { u.insert(r.0); } } u.len() }
