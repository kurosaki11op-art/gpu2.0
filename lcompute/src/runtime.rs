// L Compute runtime, step 2: device buffers, in-order streams, checked errors, over the reference interpreter. The API mirrors what a GPU runtime offers (allocate, copy, launch, synchronise).
use crate::interp::{self, Arg, Buf, Dim3};
use crate::ir::{Kernel, ParamKind};
use std::collections::HashMap;
use std::sync::mpsc::{channel, Sender};
use std::sync::{Arc, Mutex};
use std::thread::JoinHandle;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)] pub struct BufId(pub u32);
#[derive(Clone, Copy, Debug, PartialEq, Eq)] pub struct StreamId(pub usize);
#[derive(Clone, Copy, Debug)] pub enum RtArg { Buf(BufId), I32(i32), F32(f32) }

struct Mem { bufs: HashMap<u32, Box<[f32]>>, freed: Vec<u32>, next: u32 }
enum Cmd { Launch(Arc<Kernel>, Dim3, Dim3, Vec<RtArg>), CopyIn(BufId, Vec<f32>), CopyOut(BufId, Sender<Result<Vec<f32>, String>>), Fence(Sender<Result<(), String>>), Shutdown }
struct Stream { tx: Sender<Cmd>, handle: Option<JoinHandle<()>> }
#[derive(Clone, Copy, Debug, PartialEq)] pub enum Backend { Interp, Fast } // the reference interpreter, or the lockstep block executor (step 3)
pub struct Runtime { mem: Arc<Mutex<Mem>>, streams: Mutex<Vec<Stream>>, backend: Backend }

fn resolve(mem: &Mem, id: BufId) -> Result<Buf, String> {
    match mem.bufs.get(&id.0) { Some(b) => Ok(Buf { ptr: b.as_ptr() as *mut f32, len: b.len() }),
        None => Err(if mem.freed.contains(&id.0) { format!("buffer {} was freed (use after free)", id.0) } else { format!("unknown buffer handle {}", id.0) }) }
}
fn worker(mem: Arc<Mutex<Mem>>, rx: std::sync::mpsc::Receiver<Cmd>, be: Backend) {
    let mut sticky: Option<String> = None;
    while let Ok(cmd) = rx.recv() { match cmd {
        Cmd::Shutdown => break,
        Cmd::Fence(r) => { let _ = r.send(match sticky.take() { Some(e) => Err(e), None => Ok(()) }); }
        Cmd::CopyOut(id, r) => { let _ = r.send(match &sticky { Some(e) => Err(e.clone()), None => { let m = mem.lock().unwrap(); resolve(&m, id).map(|b| unsafe { std::slice::from_raw_parts(b.ptr, b.len).to_vec() }) } }); }
        Cmd::CopyIn(id, data) => { if sticky.is_none() { let m = mem.lock().unwrap(); match resolve(&m, id) { Ok(b) if b.len == data.len() => unsafe { std::ptr::copy_nonoverlapping(data.as_ptr(), b.ptr, b.len) }, Ok(b) => sticky = Some(format!("copy of {} floats into buffer {} of {}", data.len(), id.0, b.len)), Err(e) => sticky = Some(e) } } }
        Cmd::Launch(k, grid, block, args) => { if sticky.is_none() {
            let resolved: Result<Vec<Arg>, String> = { let m = mem.lock().unwrap(); args.iter().map(|a| match a { RtArg::Buf(id) => resolve(&m, *id).map(Arg::Buf), RtArg::I32(v) => Ok(Arg::I32(*v)), RtArg::F32(v) => Ok(Arg::F32(*v)) }).collect() };
            match resolved { Ok(a) => { let r = match be { Backend::Interp => interp::launch(&k, grid, block, &a), Backend::Fast => crate::fast::launch(&k, grid, block, &a) }; if let Err(e) = r { sticky = Some(e); } } Err(e) => sticky = Some(format!("{}: {}", k.name, e)) } } }
    } }
}
impl Runtime {
    pub fn new() -> Runtime { Runtime::with_backend(Backend::Interp) }
    pub fn with_backend(backend: Backend) -> Runtime { Runtime { backend, mem: Arc::new(Mutex::new(Mem { bufs: HashMap::new(), freed: Vec::new(), next: 1 })), streams: Mutex::new(Vec::new()) } }
    pub fn alloc(&self, n: usize) -> Result<BufId, String> { if n == 0 { return Err("alloc of zero floats".into()); } let mut m = self.mem.lock().unwrap(); let id = m.next; m.next += 1; m.bufs.insert(id, vec![0f32; n].into_boxed_slice()); Ok(BufId(id)) }
    // like cudaFree, freeing waits for all streams to finish first
    pub fn free(&self, id: BufId) -> Result<(), String> {
        let nstreams = self.streams.lock().unwrap().len(); // (a lock guard written inside the `for` header would be held for the whole loop and deadlock `synchronize`)
        for s in 0..nstreams { let _ = self.synchronize(StreamId(s)); }
        let mut m = self.mem.lock().unwrap(); if m.bufs.remove(&id.0).is_some() { m.freed.push(id.0); Ok(()) } else if m.freed.contains(&id.0) { Err(format!("double free of buffer {}", id.0)) } else { Err(format!("free of unknown buffer handle {}", id.0)) }
    }
    pub fn live_buffers(&self) -> usize { self.mem.lock().unwrap().bufs.len() }
    pub fn create_stream(&self) -> StreamId {
        let (tx, rx) = channel(); let mem = self.mem.clone(); let be = self.backend; let handle = std::thread::spawn(move || worker(mem, rx, be));
        let mut s = self.streams.lock().unwrap(); s.push(Stream { tx, handle: Some(handle) }); StreamId(s.len() - 1)
    }
    fn send(&self, s: StreamId, c: Cmd) -> Result<(), String> { let st = self.streams.lock().unwrap(); st.get(s.0).ok_or(format!("unknown stream {}", s.0))?.tx.send(c).map_err(|_| "stream is closed".to_string()) }
    // checks are made at enqueue time where possible (sizes, handles, argument kinds and count), so mistakes are reported where they are made
    pub fn copy_to_device(&self, s: StreamId, id: BufId, data: &[f32]) -> Result<(), String> {
        { let m = self.mem.lock().unwrap(); let b = resolve(&m, id)?; if b.len != data.len() { return Err(format!("copy of {} floats into buffer {} of {}", data.len(), id.0, b.len)); } }
        self.send(s, Cmd::CopyIn(id, data.to_vec()))
    }
    pub fn copy_to_host(&self, s: StreamId, id: BufId) -> Result<Vec<f32>, String> { let (tx, rx) = channel(); self.send(s, Cmd::CopyOut(id, tx))?; rx.recv().map_err(|_| "stream died".to_string())? }
    pub fn launch(&self, s: StreamId, k: &Arc<Kernel>, grid: Dim3, block: Dim3, args: &[RtArg]) -> Result<(), String> {
        if args.len() != k.params.len() { return Err(format!("{}: expected {} arguments, got {}", k.name, k.params.len(), args.len())); }
        { let m = self.mem.lock().unwrap(); for (i, (a, p)) in args.iter().zip(&k.params).enumerate() { match (a, p) {
            (RtArg::Buf(id), ParamKind::BufF32) => { resolve(&m, *id).map_err(|e| format!("{}: argument {}: {}", k.name, i, e))?; }
            (RtArg::I32(_), ParamKind::I32) | (RtArg::F32(_), ParamKind::F32) => {}
            _ => return Err(format!("{}: argument {} has the wrong kind (expected {:?})", k.name, i, p)) } } }
        self.send(s, Cmd::Launch(k.clone(), grid, block, args.to_vec()))
    }
    pub fn synchronize(&self, s: StreamId) -> Result<(), String> { let (tx, rx) = channel(); self.send(s, Cmd::Fence(tx))?; rx.recv().map_err(|_| "stream died".to_string())? }
}
impl Drop for Runtime { fn drop(&mut self) { let mut st = self.streams.lock().unwrap(); for s in st.iter() { let _ = s.tx.send(Cmd::Shutdown); } for s in st.iter_mut() { if let Some(h) = s.handle.take() { let _ = h.join(); } } } }
