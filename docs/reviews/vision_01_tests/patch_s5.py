import sys
s=open(sys.argv[1],encoding='utf8').read()
def rep(a,b):
    global s
    assert a in s,a
    s=s.replace(a,b)
rep('const E_HBM: f64 = 5.74;','')
rep('const LW_PEAK: f64 = 10e15;','')
rep('const PUE_AIR: f64 = 1.4; const PUE_LIQ: f64 = 1.15;','')
rep('const WAFER_PRICE: f64','''fn ev(k:&str,d:f64)->f64{std::env::var(k).ok().and_then(|v|v.parse().ok()).unwrap_or(d)}
const WAFER_PRICE: f64''')
s=s.replace('E_HBM','ev("V_HBM",5.74)').replace('LW_PEAK','ev("V_PEAK",10e15)').replace('PUE_AIR','ev("V_PUEG",1.4)').replace('PUE_LIQ','ev("V_PUEL",1.15)')
# chips(): attention MACs at their own energy, MAC overhead, logic leak, old fabric, writes, chip capex adder
a='let e = s.bytes * 8.0 * e_sram * 1e-12 + s.macs * mac_pj(bits) * 1e-12 + (0.5 + leak * gb) * n * lat + link; R { n, lat, t: lat, ej: e / b, capex: n * per_chip, pue: ev("V_PUEL",1.15), b }'
assert a in s
s=s.replace(a,'''let att = b * 2.0 * m.layers * m.d * ctxl(); let wmac = s.macs - att;
    let ibuf = ev("V_IDLE",0.0) * (0.5 + leak * gb) * n * lat;
    let e = s.bytes * 8.0 * e_sram * 1e-12 + ev("V_MACX",1.0) * (wmac * mac_pj(bits) + att * ev("V_ATTPJ", mac_pj(bits))) * 1e-12 + (ev("V_LOGICW",0.5) + leak * gb) * n * lat + ibuf + link; R { n, lat, t: lat, ej: e / b, capex: n * (per_chip + ev("V_ADD",0.0)), pue: ev("V_PUEL",1.15), b }''')
if '--oldfab' in sys.argv:
    rep('0.5e-6 * cpl.log2().ceil().max(0.0))','0.5e-6 * cpl.log2().ceil().max(1.0))')
    rep('let boundary = if cpl <= 1.0 { (n - 1.0) * LINK_S } else { 0.0 };','let boundary = 0.0;')
open(sys.argv[2],'w',encoding='utf8').write(s)
