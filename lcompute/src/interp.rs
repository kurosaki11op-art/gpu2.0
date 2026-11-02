// Reference interpreter: defines what a kernel means (docs/SPEC.md). Slow and exact. Blocks run in parallel on CPU threads; the threads of one block run one after another up to each barrier.
use crate::ir::*;
use std::collections::HashMap;
use std::sync::atomic::{AtomicUsize, Ordering};

#[derive(Clone, Copy)] pub struct Buf { pub ptr: *mut f32, pub len: usize }
unsafe impl Send for Buf {} unsafe impl Sync for Buf {}
#[derive(Clone, Copy)] pub enum Arg { Buf(Buf), I32(i32), F32(f32) }
unsafe impl Send for Arg {} unsafe impl Sync for Arg {}
#[derive(Clone, Copy, Debug)] pub struct Dim3 { pub x: usize, pub y: usize, pub z: usize }
pub fn dim(x: usize, y: usize, z: usize) -> Dim3 { Dim3 { x, y, z } }

struct Th { regs: Vec<u32>, pc: usize, done: bool, waiting: bool, tid: [usize; 3] }
fn fb(v: u32) -> f32 { f32::from_bits(v) } fn tb(v: f32) -> u32 { v.to_bits() }

fn run_block(k: &Kernel, labels: &HashMap<u32, usize>, args: &[Arg], grid: Dim3, block: Dim3, bid: [usize; 3]) -> Result<(), String> {
    let nt = block.x * block.y * block.z; let mut shared: Vec<Vec<f32>> = k.shared.iter().map(|&n| vec![0f32; n]).collect();
    let mut th: Vec<Th> = (0..nt).map(|t| Th { regs: vec![0u32; k.regs.len()], pc: 0, done: false, waiting: false, tid: [t % block.x, (t / block.x) % block.y, t / (block.x * block.y)] }).collect();
    loop {
        for t in th.iter_mut() { if t.done || t.waiting { continue; }
            loop {
                if t.pc >= k.code.len() { t.done = true; break; }
                let ins = &k.code[t.pc]; t.pc += 1;
                match ins {
                    Inst::ConstI(r, v) => t.regs[r.0 as usize] = *v as u32, Inst::ConstF(r, v) => t.regs[r.0 as usize] = tb(*v),
                    Inst::Special(r, s) => { let v = match s { Sp::Tid(a) => t.tid[*a as usize], Sp::Bid(a) => bid[*a as usize], Sp::Bdim(a) => [block.x, block.y, block.z][*a as usize], Sp::Gdim(a) => [grid.x, grid.y, grid.z][*a as usize] }; t.regs[r.0 as usize] = v as u32; }
                    Inst::ParamS(r, p) => t.regs[r.0 as usize] = match args[*p as usize] { Arg::I32(v) => v as u32, Arg::F32(v) => tb(v), Arg::Buf(_) => return Err(format!("{}: parameter {} is a buffer, not a scalar", k.name, p)) },
                    Inst::Mov(d, s) => t.regs[d.0 as usize] = t.regs[s.0 as usize],
                    Inst::BinI(d, op, a, b) => { let (x, y) = (t.regs[a.0 as usize] as i32, t.regs[b.0 as usize] as i32); t.regs[d.0 as usize] = match op { BinOp::Add => x.wrapping_add(y), BinOp::Sub => x.wrapping_sub(y), BinOp::Mul => x.wrapping_mul(y), BinOp::Div => { if y == 0 { return Err(format!("{}: integer division by zero", k.name)); } x / y } BinOp::Rem => { if y == 0 { return Err(format!("{}: integer remainder by zero", k.name)); } x % y } BinOp::Min => x.min(y), BinOp::Max => x.max(y), BinOp::And => x & y, BinOp::Or => x | y, BinOp::Shl => x << (y & 31), BinOp::Shr => x >> (y & 31) } as u32; }
                    Inst::BinF(d, op, a, b) => { let (x, y) = (fb(t.regs[a.0 as usize]), fb(t.regs[b.0 as usize])); t.regs[d.0 as usize] = tb(match op { BinOp::Add => x + y, BinOp::Sub => x - y, BinOp::Mul => x * y, BinOp::Div => x / y, BinOp::Min => x.min(y), BinOp::Max => x.max(y), _ => return Err(format!("{}: operator {:?} is not defined for floats", k.name, op)) }); }
                    Inst::CmpI(d, op, a, b) => { let (x, y) = (t.regs[a.0 as usize] as i32, t.regs[b.0 as usize] as i32); t.regs[d.0 as usize] = (match op { CmpOp::Lt => x < y, CmpOp::Le => x <= y, CmpOp::Gt => x > y, CmpOp::Ge => x >= y, CmpOp::Eq => x == y, CmpOp::Ne => x != y }) as u32; }
                    Inst::CmpF(d, op, a, b) => { let (x, y) = (fb(t.regs[a.0 as usize]), fb(t.regs[b.0 as usize])); t.regs[d.0 as usize] = (match op { CmpOp::Lt => x < y, CmpOp::Le => x <= y, CmpOp::Gt => x > y, CmpOp::Ge => x >= y, CmpOp::Eq => x == y, CmpOp::Ne => x != y }) as u32; }
                    Inst::UnF(d, op, a) => { let x = fb(t.regs[a.0 as usize]); t.regs[d.0 as usize] = tb(match op { UnOp::Neg => -x, UnOp::Abs => x.abs(), UnOp::Sqrt => x.sqrt(), UnOp::Exp => x.exp(), UnOp::Tanh => x.tanh() }); }
                    Inst::CvtIF(d, a) => t.regs[d.0 as usize] = tb(t.regs[a.0 as usize] as i32 as f32), Inst::CvtFI(d, a) => t.regs[d.0 as usize] = fb(t.regs[a.0 as usize]) as i32 as u32,
                    Inst::SelF(d, p, a, b) => t.regs[d.0 as usize] = if t.regs[p.0 as usize] != 0 { t.regs[a.0 as usize] } else { t.regs[b.0 as usize] },
                    Inst::LdG(d, p, i) => { let b = match args[*p as usize] { Arg::Buf(b) => b, _ => return Err(format!("{}: parameter {} is not a buffer", k.name, p)) }; let ix = t.regs[i.0 as usize] as i32; if ix < 0 || ix as usize >= b.len { return Err(format!("{}: out-of-range global load, index {} of {} (block {:?}, thread {:?})", k.name, ix, b.len, bid, t.tid)); } t.regs[d.0 as usize] = tb(unsafe { *b.ptr.add(ix as usize) }); }
                    Inst::StG(p, i, v) => { let b = match args[*p as usize] { Arg::Buf(b) => b, _ => return Err(format!("{}: parameter {} is not a buffer", k.name, p)) }; let ix = t.regs[i.0 as usize] as i32; if ix < 0 || ix as usize >= b.len { return Err(format!("{}: out-of-range global store, index {} of {} (block {:?}, thread {:?})", k.name, ix, b.len, bid, t.tid)); } unsafe { *b.ptr.add(ix as usize) = fb(t.regs[v.0 as usize]); } }
                    Inst::LdS(d, a, i) => { let ix = t.regs[i.0 as usize] as i32; let arr = &shared[*a as usize]; if ix < 0 || ix as usize >= arr.len() { return Err(format!("{}: out-of-range shared load, index {} of {}", k.name, ix, arr.len())); } t.regs[d.0 as usize] = tb(arr[ix as usize]); }
                    Inst::StS(a, i, v) => { let ix = t.regs[i.0 as usize] as i32; let arr = &mut shared[*a as usize]; if ix < 0 || ix as usize >= arr.len() { return Err(format!("{}: out-of-range shared store, index {} of {}", k.name, ix, arr.len())); } arr[ix as usize] = fb(t.regs[v.0 as usize]); }
                    Inst::Barrier => { t.waiting = true; break; }
                    Inst::Label(_) => {}, Inst::Br(l) => t.pc = labels[l], Inst::BrIf(p, l) => { if t.regs[p.0 as usize] != 0 { t.pc = labels[l]; } } Inst::BrIfNot(p, l) => { if t.regs[p.0 as usize] == 0 { t.pc = labels[l]; } }
                    Inst::Ret => { t.done = true; break; }
                }
            }
        }
        let waiting = th.iter().filter(|t| t.waiting).count(); let done = th.iter().filter(|t| t.done).count();
        if done == nt { return Ok(()); }
        if waiting + done == nt { if done > 0 { return Err(format!("{}: barrier divergence in block {:?}: {} thread(s) returned while {} wait at a barrier", k.name, bid, done, waiting)); } for t in th.iter_mut() { t.waiting = false; } }
        else { return Err(format!("{}: internal error: a thread neither finished nor reached a barrier", k.name)); }
    }
}

pub fn launch(k: &Kernel, grid: Dim3, block: Dim3, args: &[Arg]) -> Result<(), String> {
    if args.len() != k.params.len() { return Err(format!("{}: expected {} arguments, got {}", k.name, k.params.len(), args.len())); }
    let mut labels = HashMap::new(); for (i, ins) in k.code.iter().enumerate() { if let Inst::Label(l) = ins { labels.insert(*l, i); } }
    let nblocks = grid.x * grid.y * grid.z; let nw = std::thread::available_parallelism().map(|n| n.get()).unwrap_or(1).min(nblocks.max(1));
    let next = AtomicUsize::new(0); let err: std::sync::Mutex<Option<String>> = std::sync::Mutex::new(None);
    std::thread::scope(|s| { for _ in 0..nw { s.spawn(|| loop {
        let b = next.fetch_add(1, Ordering::Relaxed); if b >= nblocks || err.lock().unwrap().is_some() { break; }
        if let Err(e) = run_block(k, &labels, args, grid, block, [b % grid.x, (b / grid.x) % grid.y, b / (grid.x * grid.y)]) { *err.lock().unwrap() = Some(e); break; }
    }); } });
    match err.into_inner().unwrap() { Some(e) => Err(e), None => Ok(()) }
}
