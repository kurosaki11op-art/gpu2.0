// Kernel builder: a Rust API that writes IR, so kernels are written as ordinary code (the front end of version 0.1).
use crate::ir::*;
pub struct B { name: String, params: Vec<ParamKind>, shared: Vec<usize>, regs: Vec<Ty>, code: Vec<Inst>, nlabel: u32 }
impl B {
    pub fn new(name: &str) -> B { B { name: name.to_string(), params: Vec::new(), shared: Vec::new(), regs: Vec::new(), code: Vec::new(), nlabel: 0 } }
    pub fn finish(self) -> Kernel { Kernel { name: self.name, params: self.params, shared: self.shared, regs: self.regs, code: self.code } }
    fn reg(&mut self, t: Ty) -> Reg { self.regs.push(t); Reg(self.regs.len() as u32 - 1) }
    fn label(&mut self) -> u32 { self.nlabel += 1; self.nlabel - 1 }
    // parameters
    pub fn param_buf(&mut self) -> u32 { self.params.push(ParamKind::BufF32); self.params.len() as u32 - 1 }
    pub fn param_i32(&mut self) -> Reg { self.params.push(ParamKind::I32); let k = self.params.len() as u32 - 1; let r = self.reg(Ty::I32); self.code.push(Inst::ParamS(r, k)); r }
    pub fn param_f32(&mut self) -> Reg { self.params.push(ParamKind::F32); let k = self.params.len() as u32 - 1; let r = self.reg(Ty::F32); self.code.push(Inst::ParamS(r, k)); r }
    pub fn shared(&mut self, floats: usize) -> u32 { self.shared.push(floats); self.shared.len() as u32 - 1 }
    // constants and special registers
    pub fn ci(&mut self, v: i32) -> Reg { let r = self.reg(Ty::I32); self.code.push(Inst::ConstI(r, v)); r }
    pub fn cf(&mut self, v: f32) -> Reg { let r = self.reg(Ty::F32); self.code.push(Inst::ConstF(r, v)); r }
    fn sp(&mut self, s: Sp) -> Reg { let r = self.reg(Ty::I32); self.code.push(Inst::Special(r, s)); r }
    pub fn tid(&mut self, a: u8) -> Reg { self.sp(Sp::Tid(a)) } pub fn bid(&mut self, a: u8) -> Reg { self.sp(Sp::Bid(a)) }
    pub fn bdim(&mut self, a: u8) -> Reg { self.sp(Sp::Bdim(a)) } pub fn gdim(&mut self, a: u8) -> Reg { self.sp(Sp::Gdim(a)) }
    // arithmetic
    fn bi(&mut self, op: BinOp, a: Reg, b: Reg) -> Reg { let r = self.reg(Ty::I32); self.code.push(Inst::BinI(r, op, a, b)); r }
    fn bf(&mut self, op: BinOp, a: Reg, b: Reg) -> Reg { let r = self.reg(Ty::F32); self.code.push(Inst::BinF(r, op, a, b)); r }
    pub fn add_i(&mut self, a: Reg, b: Reg) -> Reg { self.bi(BinOp::Add, a, b) } pub fn sub_i(&mut self, a: Reg, b: Reg) -> Reg { self.bi(BinOp::Sub, a, b) }
    pub fn mul_i(&mut self, a: Reg, b: Reg) -> Reg { self.bi(BinOp::Mul, a, b) } pub fn div_i(&mut self, a: Reg, b: Reg) -> Reg { self.bi(BinOp::Div, a, b) }
    pub fn rem_i(&mut self, a: Reg, b: Reg) -> Reg { self.bi(BinOp::Rem, a, b) } pub fn shr_i(&mut self, a: Reg, b: Reg) -> Reg { self.bi(BinOp::Shr, a, b) }
    pub fn and_p(&mut self, a: Reg, b: Reg) -> Reg { let r = self.reg(Ty::Pred); self.code.push(Inst::BinI(r, BinOp::And, a, b)); r }
    pub fn add_f(&mut self, a: Reg, b: Reg) -> Reg { self.bf(BinOp::Add, a, b) } pub fn sub_f(&mut self, a: Reg, b: Reg) -> Reg { self.bf(BinOp::Sub, a, b) }
    pub fn mul_f(&mut self, a: Reg, b: Reg) -> Reg { self.bf(BinOp::Mul, a, b) } pub fn div_f(&mut self, a: Reg, b: Reg) -> Reg { self.bf(BinOp::Div, a, b) }
    pub fn max_f(&mut self, a: Reg, b: Reg) -> Reg { self.bf(BinOp::Max, a, b) }
    pub fn un_f(&mut self, op: UnOp, a: Reg) -> Reg { let r = self.reg(Ty::F32); self.code.push(Inst::UnF(r, op, a)); r }
    pub fn cvt_if(&mut self, a: Reg) -> Reg { let r = self.reg(Ty::F32); self.code.push(Inst::CvtIF(r, a)); r }
    pub fn lt_i(&mut self, a: Reg, b: Reg) -> Reg { let r = self.reg(Ty::Pred); self.code.push(Inst::CmpI(r, CmpOp::Lt, a, b)); r }
    pub fn gt_i(&mut self, a: Reg, b: Reg) -> Reg { let r = self.reg(Ty::Pred); self.code.push(Inst::CmpI(r, CmpOp::Gt, a, b)); r }
    pub fn sel_f(&mut self, p: Reg, t: Reg, f: Reg) -> Reg { let r = self.reg(Ty::F32); self.code.push(Inst::SelF(r, p, t, f)); r }
    // reassignable values
    pub fn mov(&mut self, dst: Reg, src: Reg) { self.code.push(Inst::Mov(dst, src)); }
    pub fn var_i(&mut self, init: Reg) -> Reg { let r = self.reg(Ty::I32); self.code.push(Inst::Mov(r, init)); r }
    pub fn var_f(&mut self, init: Reg) -> Reg { let r = self.reg(Ty::F32); self.code.push(Inst::Mov(r, init)); r }
    // memory
    pub fn load_g(&mut self, buf: u32, idx: Reg) -> Reg { let r = self.reg(Ty::F32); self.code.push(Inst::LdG(r, buf, idx)); r }
    pub fn store_g(&mut self, buf: u32, idx: Reg, v: Reg) { self.code.push(Inst::StG(buf, idx, v)); }
    pub fn load_s(&mut self, arr: u32, idx: Reg) -> Reg { let r = self.reg(Ty::F32); self.code.push(Inst::LdS(r, arr, idx)); r }
    pub fn store_s(&mut self, arr: u32, idx: Reg, v: Reg) { self.code.push(Inst::StS(arr, idx, v)); }
    pub fn barrier(&mut self) { self.code.push(Inst::Barrier); }
    pub fn ret(&mut self) { self.code.push(Inst::Ret); }
    // structured control flow built from labels and branches
    pub fn if_(&mut self, p: Reg, f: impl FnOnce(&mut B)) { let end = self.label(); self.code.push(Inst::BrIfNot(p, end)); f(self); self.code.push(Inst::Label(end)); }
    pub fn for_range(&mut self, start: Reg, end: Reg, step: i32, f: impl FnOnce(&mut B, Reg)) {
        let i = self.var_i(start); let st = self.ci(step); let (top, out) = (self.label(), self.label());
        self.code.push(Inst::Label(top)); let p = self.lt_i(i, end); self.code.push(Inst::BrIfNot(p, out)); f(self, i);
        self.code.push(Inst::BinI(i, BinOp::Add, i, st)); self.code.push(Inst::Br(top)); self.code.push(Inst::Label(out));
    }
    pub fn while_(&mut self, cond: impl FnOnce(&mut B) -> Reg, body: impl FnOnce(&mut B)) {
        let (top, out) = (self.label(), self.label()); self.code.push(Inst::Label(top)); let p = cond(self); self.code.push(Inst::BrIfNot(p, out)); body(self); self.code.push(Inst::Br(top)); self.code.push(Inst::Label(out));
    }
}
