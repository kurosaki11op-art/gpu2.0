// Fast CPU back end (step 3): a lockstep block executor. The threads of a block run together; each instruction is applied to all active threads as one loop over a per-instruction register row. Divergence: the lanes at the lowest instruction index run first, so lanes re-join; barriers are waiting points. Same meaning as interp.rs (bar C1: bit-identical outputs).
use crate::interp::{Arg, Dim3};
use crate::ir::*;
use std::sync::atomic::{AtomicUsize, Ordering};

fn fb(v: u32) -> f32 { f32::from_bits(v) } fn tb(v: f32) -> u32 { v.to_bits() }
// dense helper: all lanes active; works on 8-lane chunks copied into small arrays so the compiler can vectorise without worrying about overlap of d with a or b
#[inline(always)] unsafe fn bin(rp: *mut u32, nt: usize, d: usize, a: usize, b: usize, f: impl Fn(u32, u32) -> u32) {
    let (pd, pa, pb) = (rp.add(d * nt), rp.add(a * nt), rp.add(b * nt)); let mut t = 0;
    while t + 8 <= nt { let mut x = [0u32; 8]; let mut y = [0u32; 8]; for i in 0..8 { x[i] = *pa.add(t + i); y[i] = *pb.add(t + i); } for i in 0..8 { x[i] = f(x[i], y[i]); } for i in 0..8 { *pd.add(t + i) = x[i]; } t += 8; }
    while t < nt { *pd.add(t) = f(*pa.add(t), *pb.add(t)); t += 1; }
}

unsafe fn run_block(k: &Kernel, labels: &[usize], args: &[Arg], grid: Dim3, block: Dim3, bid: [usize; 3]) -> Result<(), String> {
    let nt = block.x * block.y * block.z; let mut regs = vec![0u32; k.regs.len() * nt]; let mut shared: Vec<Vec<f32>> = k.shared.iter().map(|&n| vec![0f32; n]).collect();
    let tid: Vec<[usize; 3]> = (0..nt).map(|t| [t % block.x, (t / block.x) % block.y, t / (block.x * block.y)]).collect();
    let mut pc = vec![0usize; nt]; let mut done = vec![false; nt]; let mut waiting = vec![false; nt];
    let mut act: Vec<usize> = (0..nt).collect(); let mut diverged = false; let mut ndone = 0usize;
    macro_rules! lanes { ($t:ident, $body:block) => { if act.len() == nt { for $t in 0..nt $body } else { for &$t in act.iter() $body } } }
    let mut stale = false; let mut upc = 0usize; let rp = regs.as_mut_ptr(); let sptr: Vec<(*mut f32, usize)> = shared.iter_mut().map(|v| (v.as_mut_ptr(), v.len())).collect(); macro_rules! r { ($reg:expr, $t:expr) => { (*rp.add($reg.0 as usize * nt + $t)) } }
    macro_rules! bin2 { ($d:expr, $a:expr, $b:expr, $f:expr) => { if act.len() == nt { bin(rp, nt, $d.0 as usize, $a.0 as usize, $b.0 as usize, $f) } else { for &t in act.iter() { r!($d, t) = $f(r!($a, t), r!($b, t)); } } } }
    loop {
        if diverged || act.is_empty() {
            if stale { pc.fill(upc); stale = false; }
            let mut minpc = usize::MAX; for t in 0..nt { if !done[t] && !waiting[t] && pc[t] < minpc { minpc = pc[t]; } }
            if minpc == usize::MAX {
                let nwait = (0..nt).filter(|&t| waiting[t]).count();
                if ndone == nt { return Ok(()); }
                if ndone > 0 { return Err(format!("{}: barrier divergence in block {:?}: {} thread(s) returned while {} wait at a barrier", k.name, bid, ndone, nwait)); }
                let p0 = (0..nt).find(|&t| waiting[t]).map(|t| pc[t]).unwrap(); if (0..nt).any(|t| waiting[t] && pc[t] != p0) { return Err(format!("{}: barrier divergence in block {:?}: threads wait at different barriers", k.name, bid)); }
                for t in 0..nt { waiting[t] = false; } act = (0..nt).collect(); diverged = false; continue;
            }
            act = (0..nt).filter(|&t| !done[t] && !waiting[t] && pc[t] == minpc).collect(); let sched = (0..nt).filter(|&t| !done[t] && !waiting[t]).count(); diverged = act.len() != sched;
        }
        let p = if stale { upc } else { pc[act[0]] }; if p >= k.code.len() { for &t in act.iter() { done[t] = true; ndone += 1; } diverged = true; continue; }
        let ins = &k.code[p]; let mut next = p + 1;
        match ins {
            Inst::ConstI(d, v) => { lanes!(t, { r!(d, t) = *v as u32; }) } Inst::ConstF(d, v) => { let b = tb(*v); lanes!(t, { r!(d, t) = b; }) }
            Inst::Special(d, s) => { lanes!(t, { r!(d, t) = (match s { Sp::Tid(a) => tid[t][*a as usize], Sp::Bid(a) => bid[*a as usize], Sp::Bdim(a) => [block.x, block.y, block.z][*a as usize], Sp::Gdim(a) => [grid.x, grid.y, grid.z][*a as usize] }) as u32; }) }
            Inst::ParamS(d, pi) => { let v = match args[*pi as usize] { Arg::I32(v) => v as u32, Arg::F32(v) => tb(v), Arg::Buf(_) => return Err(format!("{}: parameter {} is a buffer, not a scalar", k.name, pi)) }; lanes!(t, { r!(d, t) = v; }) }
            Inst::Mov(d, s) => { if act.len() == nt { std::ptr::copy(rp.add(s.0 as usize * nt), rp.add(d.0 as usize * nt), nt); } else { lanes!(t, { r!(d, t) = r!(s, t); }) } }
            Inst::BinI(d, op, a, b) => { match op {
                BinOp::Add => bin2!(d, a, b, |x: u32, y: u32| (x as i32).wrapping_add(y as i32) as u32), BinOp::Sub => bin2!(d, a, b, |x: u32, y: u32| (x as i32).wrapping_sub(y as i32) as u32),
                BinOp::Mul => bin2!(d, a, b, |x: u32, y: u32| (x as i32).wrapping_mul(y as i32) as u32), BinOp::Min => bin2!(d, a, b, |x: u32, y: u32| (x as i32).min(y as i32) as u32), BinOp::Max => bin2!(d, a, b, |x: u32, y: u32| (x as i32).max(y as i32) as u32),
                BinOp::And => bin2!(d, a, b, |x: u32, y: u32| x & y), BinOp::Or => bin2!(d, a, b, |x: u32, y: u32| x | y),
                BinOp::Shl => bin2!(d, a, b, |x: u32, y: u32| ((x as i32) << (y & 31)) as u32), BinOp::Shr => bin2!(d, a, b, |x: u32, y: u32| ((x as i32) >> (y & 31)) as u32),
                BinOp::Div => lanes!(t, { let y = r!(b, t) as i32; if y == 0 { return Err(format!("{}: integer division by zero", k.name)); } r!(d, t) = (r!(a, t) as i32 / y) as u32; }),
                BinOp::Rem => lanes!(t, { let y = r!(b, t) as i32; if y == 0 { return Err(format!("{}: integer remainder by zero", k.name)); } r!(d, t) = (r!(a, t) as i32 % y) as u32; }) } }
            Inst::BinF(d, op, a, b) => { match op {
                BinOp::Add => bin2!(d, a, b, |x: u32, y: u32| tb(fb(x) + fb(y))), BinOp::Sub => bin2!(d, a, b, |x: u32, y: u32| tb(fb(x) - fb(y))), BinOp::Mul => bin2!(d, a, b, |x: u32, y: u32| tb(fb(x) * fb(y))),
                BinOp::Div => bin2!(d, a, b, |x: u32, y: u32| tb(fb(x) / fb(y))), BinOp::Min => bin2!(d, a, b, |x: u32, y: u32| tb(fb(x).min(fb(y)))), BinOp::Max => bin2!(d, a, b, |x: u32, y: u32| tb(fb(x).max(fb(y)))),
                _ => return Err(format!("{}: operator {:?} is not defined for floats", k.name, op)) } }
            Inst::CmpI(d, op, a, b) => { match op {
                CmpOp::Lt => bin2!(d, a, b, |x: u32, y: u32| ((x as i32) < (y as i32)) as u32), CmpOp::Le => bin2!(d, a, b, |x: u32, y: u32| ((x as i32) <= (y as i32)) as u32), CmpOp::Gt => bin2!(d, a, b, |x: u32, y: u32| ((x as i32) > (y as i32)) as u32),
                CmpOp::Ge => bin2!(d, a, b, |x: u32, y: u32| ((x as i32) >= (y as i32)) as u32), CmpOp::Eq => bin2!(d, a, b, |x: u32, y: u32| (x == y) as u32), CmpOp::Ne => bin2!(d, a, b, |x: u32, y: u32| (x != y) as u32) } }
            Inst::CmpF(d, op, a, b) => { lanes!(t, { let (x, y) = (fb(r!(a, t)), fb(r!(b, t))); r!(d, t) = (match op { CmpOp::Lt => x < y, CmpOp::Le => x <= y, CmpOp::Gt => x > y, CmpOp::Ge => x >= y, CmpOp::Eq => x == y, CmpOp::Ne => x != y }) as u32; }) }
            Inst::UnF(d, op, a) => { lanes!(t, { let x = fb(r!(a, t)); r!(d, t) = tb(match op { UnOp::Neg => -x, UnOp::Abs => x.abs(), UnOp::Sqrt => x.sqrt(), UnOp::Exp => x.exp(), UnOp::Tanh => x.tanh() }); }) }
            Inst::CvtIF(d, a) => { lanes!(t, { r!(d, t) = tb(r!(a, t) as i32 as f32); }) } Inst::CvtFI(d, a) => { lanes!(t, { r!(d, t) = fb(r!(a, t)) as i32 as u32; }) }
            Inst::SelF(d, pr, a, b) => { lanes!(t, { r!(d, t) = if r!(pr, t) != 0 { r!(a, t) } else { r!(b, t) }; }) }
            Inst::LdG(d, pi, i) => { let b = match args[*pi as usize] { Arg::Buf(b) => b, _ => return Err(format!("{}: parameter {} is not a buffer", k.name, pi)) };
                lanes!(t, { let ix = r!(i, t) as i32; if ix < 0 || ix as usize >= b.len { return Err(format!("{}: out-of-range global load, index {} of {} (block {:?}, thread {:?})", k.name, ix, b.len, bid, tid[t])); } r!(d, t) = tb(unsafe { *b.ptr.add(ix as usize) }); }) }
            Inst::StG(pi, i, v) => { let b = match args[*pi as usize] { Arg::Buf(b) => b, _ => return Err(format!("{}: parameter {} is not a buffer", k.name, pi)) };
                lanes!(t, { let ix = r!(i, t) as i32; if ix < 0 || ix as usize >= b.len { return Err(format!("{}: out-of-range global store, index {} of {} (block {:?}, thread {:?})", k.name, ix, b.len, bid, tid[t])); } unsafe { *b.ptr.add(ix as usize) = fb(r!(v, t)); } }) }
            Inst::LdS(d, ai, i) => { let (sp, len) = sptr[*ai as usize];
                // dense case: one pass checks every index, then the loads run without per-lane checks; on any bad index the checked loop below reports it
                if act.len() == nt && { let mut bad = 0u32; for t in 0..nt { let ix = r!(i, t) as i32; bad |= (ix < 0 || ix as usize >= len) as u32; } bad == 0 } { for t in 0..nt { r!(d, t) = tb(*sp.add(r!(i, t) as usize)); } }
                else { lanes!(t, { let ix = r!(i, t) as i32; if ix < 0 || ix as usize >= len { return Err(format!("{}: out-of-range shared load, index {} of {}", k.name, ix, len)); } r!(d, t) = tb(*sp.add(ix as usize)); }) } }
            Inst::StS(ai, i, v) => { let (sp, len) = sptr[*ai as usize]; lanes!(t, { let ix = r!(i, t) as i32; if ix < 0 || ix as usize >= len { return Err(format!("{}: out-of-range shared store, index {} of {}", k.name, ix, len)); } *sp.add(ix as usize) = fb(r!(v, t)); }) }
            Inst::Label(_) => {}
            Inst::Br(l) => { next = labels[*l as usize]; }
            Inst::BrIf(pr, l) | Inst::BrIfNot(pr, l) => { let want = matches!(ins, Inst::BrIf(..)); let target = labels[*l as usize]; let mut taken = 0usize; let n = act.len();
                let cnt = if n == nt { let mut c = 0u32; for t in 0..nt { c += ((r!(pr, t) != 0) == want) as u32; } c as usize } else { usize::MAX }; // dense case: count lanes that branch (vectorised); all or none keeps the lanes together
                if cnt == nt { next = target; } else if cnt == 0 { next = p + 1; } else {
                for &t in act.iter() { let go = (r!(pr, t) != 0) == want; if go { pc[t] = target; taken += 1; } else { pc[t] = p + 1; } }
                if taken != 0 && taken != n { diverged = true; } next = usize::MAX; /* pcs already set */ } }
            Inst::Barrier => { for &t in act.iter() { waiting[t] = true; pc[t] = p + 1; } diverged = true; next = usize::MAX; }
            Inst::Ret => { for &t in act.iter() { done[t] = true; ndone += 1; } diverged = true; next = usize::MAX; }
        }
        if next != usize::MAX { if act.len() == nt { upc = next; stale = true; } else { for &t in act.iter() { pc[t] = next; } } } else { stale = false; } // `stale`: all lanes are at `upc` and the pc array has not been written (it is filled only when needed)
    }
}

pub fn launch(k: &Kernel, grid: Dim3, block: Dim3, args: &[Arg]) -> Result<(), String> {
    if args.len() != k.params.len() { return Err(format!("{}: expected {} arguments, got {}", k.name, k.params.len(), args.len())); }
    let nl = k.code.iter().filter_map(|i| if let Inst::Label(l) = i { Some(*l as usize + 1) } else { None }).max().unwrap_or(0); let mut labels = vec![0usize; nl]; for (i, ins) in k.code.iter().enumerate() { if let Inst::Label(l) = ins { labels[*l as usize] = i; } }
    let nblocks = grid.x * grid.y * grid.z; let nw = std::thread::available_parallelism().map(|n| n.get()).unwrap_or(1).min(nblocks.max(1));
    let next = AtomicUsize::new(0); let err: std::sync::Mutex<Option<String>> = std::sync::Mutex::new(None);
    std::thread::scope(|s| { for _ in 0..nw { s.spawn(|| loop {
        let b = next.fetch_add(1, Ordering::Relaxed); if b >= nblocks || err.lock().unwrap().is_some() { break; }
        if let Err(e) = unsafe { run_block(k, &labels, args, grid, block, [b % grid.x, (b / grid.x) % grid.y, b / (grid.x * grid.y)]) } { *err.lock().unwrap() = Some(e); break; }
    }); } });
    match err.into_inner().unwrap() { Some(e) => Err(e), None => Ok(()) }
}
