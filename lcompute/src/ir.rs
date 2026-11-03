// L Compute intermediate language, version 0.1 (see docs/SPEC.md). A flat, register-based instruction list with labels and branches (the same shape as PTX).
#[derive(Clone, Copy, Debug, PartialEq)] pub enum Ty { I32, F32, Pred }
#[derive(Clone, Copy, Debug, PartialEq)] pub struct Reg(pub u32);
#[derive(Clone, Copy, Debug)] pub enum Sp { Tid(u8), Bid(u8), Bdim(u8), Gdim(u8) } // axis 0 = x, 1 = y, 2 = z
#[derive(Clone, Copy, Debug, PartialEq)] pub enum BinOp { Add, Sub, Mul, Div, Rem, Min, Max, And, Or, Shl, Shr }
#[derive(Clone, Copy, Debug, PartialEq)] pub enum CmpOp { Lt, Le, Gt, Ge, Eq, Ne }
#[derive(Clone, Copy, Debug, PartialEq)] pub enum UnOp { Neg, Abs, Sqrt, Exp, Tanh }
#[derive(Clone, Debug)]
pub enum Inst {
    ConstI(Reg, i32), ConstF(Reg, f32), Special(Reg, Sp), ParamS(Reg, u32), Mov(Reg, Reg),
    Fma(Reg, Reg, Reg, Reg), // dst = a * b + c with ONE rounding (fused multiply-add, IEEE fma); results differ from separate multiply and add
    AddImm(Reg, Reg, i32), // dst = src + constant (wrapping); written only by the optimiser (opt.rs), never by the builder
    BinI(Reg, BinOp, Reg, Reg), BinF(Reg, BinOp, Reg, Reg), CmpI(Reg, CmpOp, Reg, Reg), CmpF(Reg, CmpOp, Reg, Reg),
    UnF(Reg, UnOp, Reg), CvtIF(Reg, Reg), CvtFI(Reg, Reg), SelF(Reg, Reg, Reg, Reg), // SelF(dst, pred, if_true, if_false)
    LdG(Reg, u32, Reg), StG(u32, Reg, Reg),  // LdG(dst, buffer parameter, index), StG(buffer parameter, index, value)
    LdS(Reg, u32, Reg), StS(u32, Reg, Reg),  // shared memory array id, index
    Barrier, Label(u32), Br(u32), BrIf(Reg, u32), BrIfNot(Reg, u32), Ret,
}
#[derive(Clone, Copy, Debug, PartialEq)] pub enum ParamKind { BufF32, I32, F32 }
#[derive(Clone, Debug)]
pub struct Kernel { pub name: String, pub params: Vec<ParamKind>, pub shared: Vec<usize>, pub regs: Vec<Ty>, pub code: Vec<Inst>, pub bounds: Option<[usize; 3]> } // bounds: the only thread-block shape the kernel may be launched with (declared by the kernel; every back end rejects another shape; the range analysis relies on it)
