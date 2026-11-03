// L Compute range analysis (step 4d, bar Q8). Interval arithmetic over the IR: for every register, the smallest interval of values it can hold at each instruction, found by a fixpoint over the control-flow graph
// (loops: after a few visits a bound that keeps growing is widened to the end of the i32 range; the condition `i < end` of a loop branch narrows i inside the loop).
// Use: a shared-memory access whose index interval lies inside the array is PROVED safe, and the PTX back end emits no check for it. Everything not proved keeps its check.
// Soundness rules: any arithmetic that could wrap the i32 range gives the full range; operations the analysis does not understand give the full range; all registers start as the full range; unreachable code is never "proved".
// The thread-block shape comes from the kernel's declared launch bounds (every back end rejects another shape); without declared bounds thread ids are only known to be non-negative.
use crate::ir::*;
use std::collections::VecDeque;

#[derive(Clone, Copy, PartialEq, Debug)] struct Iv { lo: i64, hi: i64 }
const MIN: i64 = i32::MIN as i64; const MAX: i64 = i32::MAX as i64; const TOP: Iv = Iv { lo: MIN, hi: MAX };
fn cst(v: i64) -> Iv { Iv { lo: v, hi: v } }
fn fit(lo: i64, hi: i64) -> Iv { if lo < MIN || hi > MAX { TOP } else { Iv { lo, hi } } }
fn hull(a: Iv, b: Iv) -> Iv { Iv { lo: a.lo.min(b.lo), hi: a.hi.max(b.hi) } }
fn single(a: Iv) -> Option<i64> { if a.lo == a.hi { Some(a.lo) } else { None } }

fn bin(op: BinOp, a: Iv, b: Iv) -> Iv { match op {
    BinOp::Add => fit(a.lo + b.lo, a.hi + b.hi), BinOp::Sub => fit(a.lo - b.hi, a.hi - b.lo),
    BinOp::Mul => { let p = [a.lo * b.lo, a.lo * b.hi, a.hi * b.lo, a.hi * b.hi]; fit(*p.iter().min().unwrap(), *p.iter().max().unwrap()) }
    BinOp::Min => Iv { lo: a.lo.min(b.lo), hi: a.hi.min(b.hi) }, BinOp::Max => Iv { lo: a.lo.max(b.lo), hi: a.hi.max(b.hi) },
    BinOp::And => if let Some(m) = single(b).filter(|&m| m >= 0) { Iv { lo: 0, hi: m } } else if let Some(m) = single(a).filter(|&m| m >= 0) { Iv { lo: 0, hi: m } } else if a.lo >= 0 && b.lo >= 0 { Iv { lo: 0, hi: a.hi.min(b.hi) } } else { TOP },
    BinOp::Or => if a.lo >= 0 && b.lo >= 0 { let m = a.hi.max(b.hi); Iv { lo: a.lo.max(b.lo), hi: (((m + 1) as u64).next_power_of_two() as i64 - 1).min(MAX) } } else { TOP },
    BinOp::Shl => match single(b) { Some(s) => { let s = (s & 31) as u32; fit(a.lo << s, a.hi << s) } None => TOP },
    BinOp::Shr => match single(b) { Some(s) => { let s = (s & 31) as u32; Iv { lo: a.lo >> s, hi: a.hi >> s } } None => TOP },
    BinOp::Div => if b.lo > 0 { let p = [a.lo / b.lo, a.lo / b.hi, a.hi / b.lo, a.hi / b.hi]; Iv { lo: *p.iter().min().unwrap(), hi: *p.iter().max().unwrap() } } else { TOP },
    BinOp::Rem => if b.lo > 0 { let m = b.hi - 1; if a.lo >= 0 { Iv { lo: 0, hi: a.hi.min(m) } } else { Iv { lo: a.lo.max(-m), hi: if a.hi >= 0 { a.hi.min(m) } else { 0 } } } } else { TOP },
} }

fn def_of(ins: &Inst) -> Option<Reg> { use Inst::*; match ins { ConstI(d, _) | ConstF(d, _) | Special(d, _) | ParamS(d, _) | Mov(d, _) | AddImm(d, _, _) | BinI(d, _, _, _) | BinF(d, _, _, _) | CmpI(d, _, _, _) | CmpF(d, _, _, _)
        | UnF(d, _, _) | CvtIF(d, _) | CvtFI(d, _) | SelF(d, _, _, _) | Fma(d, _, _, _) | LdG(d, _, _) | LdS(d, _, _) => Some(*d), _ => None } }

fn transfer(ins: &Inst, s: &mut Vec<Iv>, bounds: Option<[usize; 3]>) {
    use Inst::*;
    let v = match ins {
        ConstI(_, v) => cst(*v as i64),
        Special(_, sp) => match sp { Sp::Tid(a) => bounds.map(|b| Iv { lo: 0, hi: b[*a as usize] as i64 - 1 }).unwrap_or(Iv { lo: 0, hi: MAX }), Sp::Bid(_) => Iv { lo: 0, hi: MAX },
            Sp::Bdim(a) => bounds.map(|b| cst(b[*a as usize] as i64)).unwrap_or(Iv { lo: 1, hi: MAX }), Sp::Gdim(_) => Iv { lo: 1, hi: MAX } },
        Mov(_, a) => s[a.0 as usize], AddImm(_, a, c) => { let x = s[a.0 as usize]; fit(x.lo + *c as i64, x.hi + *c as i64) }
        BinI(_, op, a, b) => bin(*op, s[a.0 as usize], s[b.0 as usize]),
        CmpI(..) | CmpF(..) => Iv { lo: 0, hi: 1 },
        _ => TOP,
    };
    let d = match ins { ConstI(d, _) | ConstF(d, _) | Special(d, _) | ParamS(d, _) | Mov(d, _) | AddImm(d, _, _) | BinI(d, _, _, _) | BinF(d, _, _, _) | CmpI(d, _, _, _) | CmpF(d, _, _, _)
        | UnF(d, _, _) | CvtIF(d, _) | CvtFI(d, _) | SelF(d, _, _, _) | Fma(d, _, _, _) | LdG(d, _, _) | LdS(d, _, _) => Some(*d), _ => None };
    if let Some(d) = d { s[d.0 as usize] = v; }
}

/// For every instruction: true if it is a shared-memory load or store proved to be in range for every thread and every execution.
pub fn safe_shared(k: &Kernel) -> Vec<bool> { analyse(k).0 }

// the states that flow out of instruction i (with the given entry state): one per successor
fn successors(k: &Kernel, i: usize, s: &Vec<Iv>, label_at: &std::collections::HashMap<u32, usize>) -> Vec<(usize, Vec<Iv>)> {
    let n = k.code.len(); let mut out = Vec::new();
    match &k.code[i] {
        Inst::Ret => {}
        Inst::Br(l) => out.push((label_at[l], s.clone())),
        Inst::BrIf(p, l) | Inst::BrIfNot(p, l) => {
            let on_true_goes = matches!(k.code[i], Inst::BrIf(..)); let target = label_at[l];
            // the two outgoing states, narrowed by the comparison that made the predicate (only the pattern `p = (a < b)` directly before the branch)
            let (mut s_true, mut s_false) = (Some(s.clone()), Some(s.clone()));
            if i > 0 { if let Inst::CmpI(q, CmpOp::Lt, a, b) = &k.code[i - 1] { if q == p && a != b && a != q && b != q {
                let (ia, ib) = (s[a.0 as usize], s[b.0 as usize]);
                let t_a = Iv { lo: ia.lo, hi: ia.hi.min(ib.hi - 1) }; let t_b = Iv { lo: ib.lo.max(ia.lo + 1), hi: ib.hi }; // a < b
                s_true = if t_a.lo <= t_a.hi && t_b.lo <= t_b.hi { let mut x = s.clone(); x[a.0 as usize] = t_a; x[b.0 as usize] = t_b; Some(x) } else { None };
                let f_a = Iv { lo: ia.lo.max(ib.lo), hi: ia.hi }; let f_b = Iv { lo: ib.lo, hi: ib.hi.min(ia.hi) }; // a >= b
                s_false = if f_a.lo <= f_a.hi && f_b.lo <= f_b.hi { let mut x = s.clone(); x[a.0 as usize] = f_a; x[b.0 as usize] = f_b; Some(x) } else { None };
            } } }
            let (taken, fall) = if on_true_goes { (s_true, s_false) } else { (s_false, s_true) };
            if let Some(t) = taken { out.push((target, t)); } if i + 1 < n { if let Some(f) = fall { out.push((i + 1, f)); } }
        }
        ins => { let mut s2 = s.clone(); transfer(ins, &mut s2, k.bounds); if i + 1 < n { out.push((i + 1, s2)); } }
    }
    out
}

/// (proved flags, for every shared access: instruction number, interval of its index, array length)
pub fn analyse(k: &Kernel) -> (Vec<bool>, Vec<(usize, i64, i64, usize)>) {
    let n = k.code.len(); let nr = k.regs.len(); let mut out = vec![false; n]; let mut detail = Vec::new(); if n == 0 { return (out, detail); }
    let mut label_at = std::collections::HashMap::new(); for (i, ins) in k.code.iter().enumerate() { if let Inst::Label(l) = ins { label_at.insert(*l, i); } }
    // loop heads: labels that a later branch jumps back to; widening happens only there
    let mut is_head = vec![false; n]; let mut loop_end = vec![0usize; n];
    for (j, ins) in k.code.iter().enumerate() { if let Inst::Br(l) | Inst::BrIf(_, l) | Inst::BrIfNot(_, l) = ins { let t = label_at[l]; if t <= j { is_head[t] = true; loop_end[t] = loop_end[t].max(j); } } }
    // a loop can only make a register grow without bound if the loop writes it: widen only those registers at that loop's head (an outer counter creeping through an inner loop head is not widened there)
    let written: Vec<Vec<bool>> = (0..n).map(|t| { let mut w = vec![false; nr]; if is_head[t] { for ins in &k.code[t..=loop_end[t]] { if let Some(d) = def_of(ins) { w[d.0 as usize] = true; } } } w }).collect();
    let mut states: Vec<Option<Vec<Iv>>> = vec![None; n]; let mut visits = vec![0u32; n]; let mut queue: VecDeque<usize> = VecDeque::new();
    states[0] = Some(vec![TOP; nr]); queue.push_back(0);
    // phase 1: ascending fixpoint with widening at loop heads
    while let Some(i) = queue.pop_front() {
        let s = match &states[i] { Some(s) => s.clone(), None => continue };
        for (t, st) in successors(k, i, &s, &label_at) {
            match &states[t] { None => { states[t] = Some(st); queue.push_back(t); }
                Some(old) => { let mut new: Vec<Iv> = old.iter().zip(&st).map(|(a, b)| hull(*a, *b)).collect();
                    if new != *old { visits[t] += 1; if visits[t] > 3 && is_head[t] { for r in 0..nr { if !written[t][r] { continue; } if new[r].lo < old[r].lo { new[r].lo = MIN; } if new[r].hi > old[r].hi { new[r].hi = MAX; } } }
                        states[t] = Some(new); queue.push_back(t); } } }
        }
    }
    // phase 2: narrowing. The widened solution is sound; recomputing every state from its predecessors' outputs (which re-applies the loop conditions) and intersecting with the old state stays sound and recovers the precision lost at nested loop heads
    for _ in 0..6 {
        let mut incoming: Vec<Option<Vec<Iv>>> = vec![None; n]; incoming[0] = Some(vec![TOP; nr]);
        for i in 0..n { if let Some(s) = &states[i] { for (t, st) in successors(k, i, s, &label_at) { incoming[t] = Some(match incoming[t].take() { None => st, Some(o) => o.iter().zip(&st).map(|(a, b)| hull(*a, *b)).collect() }); } } }
        let mut changed = false;
        for t in 0..n { if let (Some(old), Some(inc)) = (&states[t], &incoming[t]) { let met: Vec<Iv> = old.iter().zip(inc).map(|(a, b)| Iv { lo: a.lo.max(b.lo), hi: a.hi.min(b.hi) }).collect();
            if met.iter().any(|v| v.lo > v.hi) { continue; } if met != *old { changed = true; states[t] = Some(met); } } }
        if !changed { break; }
    }
    for (i, ins) in k.code.iter().enumerate() { if let Some(st) = &states[i] { match ins {
        Inst::LdS(_, a, ix) | Inst::StS(a, ix, _) => { let iv = st[ix.0 as usize]; out[i] = iv.lo >= 0 && iv.hi < k.shared[*a as usize] as i64; detail.push((i, iv.lo, iv.hi, k.shared[*a as usize])); }
        _ => {} } } }
    (out, detail)
}
/// (proved, total) shared-memory accesses
pub fn coverage(k: &Kernel) -> (usize, usize) { let safe = safe_shared(k); let mut tot = 0; let mut pr = 0; for (i, ins) in k.code.iter().enumerate() { if matches!(ins, Inst::LdS(..) | Inst::StS(..)) { tot += 1; if safe[i] { pr += 1; } } } (pr, tot) }
