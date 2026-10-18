const pptxgen = require("pptxgenjs");
const { applyTheme } = require(process.env.SK + "/scripts/apply_theme.js");
const THEME = { name: "SPARK Cortex", headFontFace: "Cambria", bodyFontFace: "Calibri",
  colors: { dk1: "151A3D", lt1: "FFFFFF", dk2: "2B3270", lt2: "EEF0FA", accent1: "F2A93B", accent2: "5B6BD6", accent3: "2FA37A", accent4: "D9534F", accent5: "8A93C9", accent6: "6B7280", hlink: "5B6BD6", folHlink: "8A93C9" } };
const pres = new pptxgen(); pres.layout = "LAYOUT_16x9"; pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "SPARK Cortex"; pres.author = "L Lawliet (Navin), CKCET";
const C = pres.SchemeColor;
pres.defineSlideMaster({ title: "LIGHT", background: { color: C.background1 },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.3, w: 9, h: 0.9, fontFace: "Cambria", fontSize: 30, bold: true, color: C.text1, align: "left", valign: "middle", margin: 0 }, text: "" } }],
  slideNumber: { x: 9.2, y: 5.25, color: C.accent6, fontSize: 10 } });
pres.defineSlideMaster({ title: "DARK", background: { color: C.text1 },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: 0.6, y: 1.5, w: 8.8, h: 1.4, fontFace: "Cambria", fontSize: 40, bold: true, color: C.background1, align: "left", valign: "middle", margin: 0 }, text: "" } }] });
const lab = (s, t, x, y, w, color, size, bold, extra) => s.addText(t, Object.assign({ x, y, w, h: 0.4, fontSize: size || 14, color: color || C.text1, bold: !!bold, margin: 0, isTextBox: true, valign: "top", fontFace: "Calibri" }, extra || {}));
const chartBase = (title) => ({ showTitle: true, title, titleFontSize: 14, titleColor: "151A3D", titleFontFace: "+mn-lt", catAxisLabelColor: "2B3270", valAxisLabelColor: "6B7280", catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", catAxisLabelFontSize: 12, valAxisLabelFontSize: 11, valGridLine: { color: "DDE0F0", size: 0.5 }, catGridLine: { style: "none" }, showValue: true, dataLabelFontSize: 11, dataLabelColor: "151A3D", dataLabelFontFace: "+mn-lt", dataLabelFormatCode: "0.0", valAxisMinVal: 0, valAxisMaxVal: 100, showLegend: true, legendPos: "b", legendFontSize: 12, legendFontFace: "+mn-lt", legendColor: "2B3270", barGapWidthPct: 60 });
const card = (s, x, y, w, h, fill) => s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill || C.background2 }, line: { color: fill || C.background2, width: 0 }, rectRadius: 0.1, objectName: "card" });
const NUM = { digits: "digits", clothing: "clothing", words: "spoken words" };

// 1 cover
pres.addSection({ title: "Open" });
let s = pres.addSlide({ masterName: "DARK", sectionTitle: "Open" });
s.addText("SPARK Cortex", { placeholder: "title" });
lab(s, "A brain-principled chip that keeps learning after it ships", 0.6, 2.95, 8.8, C.accent1, 22, false, { italic: true, h: 0.5 });
lab(s, "L Lawliet  |  Navin (Kakashi), CKCET  |  PALS innoWAH! 2026-27", 0.6, 4.4, 8.8, C.accent5, 14);
lab(s, "Every number in this deck is labelled SIMULATED, ESTIMATED or MEASURED. Nothing is measured on hardware yet.", 0.6, 4.8, 8.8, C.accent5, 12);
s.addNotes("Hello judges. We are L Lawliet from CKCET. SPARK Cortex is a small chip that learns new things after it has shipped, without forgetting the old ones, and without a multiplier or backpropagation. One promise before we start: every number I show is labelled as simulated, estimated or measured, and nothing is measured on hardware yet.");

// 2 problem
pres.addSection({ title: "Why" });
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Why" });
s.addText("AI stops learning the day it ships", { placeholder: "title" });
const stat = (x, big, small, col) => { card(s, x, 1.5, 2.8, 2.3); lab(s, big, x + 0.2, 1.7, 2.4, col, 54, true, { h: 1.0, fontFace: "Cambria" }); lab(s, small, x + 0.2, 2.85, 2.4, C.text1, 14, false, { h: 0.9 }); };
stat(0.5, "19.5%", "digits: a network that learns in 5 stages forgets the earlier ones", C.accent4);
stat(3.6, "20.0%", "clothing: same test, same forgetting", C.accent4);
stat(6.7, "15.9%", "spoken words: same test, same forgetting", C.accent4);
lab(s, "Fixing it today means retraining from scratch: more energy, more heat, and hardware that is thrown away when it can no longer be updated. A chip that can learn in the field avoids that.", 0.5, 4.1, 9, C.text1, 16, false, { h: 1.0 });
s.addNotes("A normal neural network learns once. Teach it five new things in five stages and it keeps only the last stage: 19.5 percent on digits, 20 on clothing, 16 on spoken words (simulated, 5 seeds). The usual fix is to retrain from scratch, which costs energy and, in the end, hardware that is discarded. We asked what a chip would look like if it could keep learning like a brain.");

// 3 idea
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Why" });
s.addText("The idea: a human brain, as a chip", { placeholder: "title" });
const rows = [["Senses", "Eyes and ears turn raw pixels and sound into a sparse code. Detectors learn by themselves, no labels."], ["Learn once", "Each example is counted into a small fast table. No backpropagation, no multiplier, no matrices."], ["Dream and sleep", "Old classes are replayed from 10-bit counters, so nothing is stored. The night ends by itself."], ["Share", "A second chip can take over the memory, or two memories merge by adding counts."]];
rows.forEach((r, i) => { const y = 1.4 + i * 0.95; card(s, 0.5, y, 9, 0.8); s.addShape(pres.shapes.OVAL, { x: 0.65, y: y + 0.15, w: 0.5, h: 0.5, fill: { color: C.accent1 }, line: { color: C.accent1, width: 0 }, objectName: "marker" }); lab(s, String(i + 1), 0.65, y + 0.2, 0.5, C.text1, 18, true, { align: "center", h: 0.4 }); lab(s, r[0], 1.35, y + 0.08, 1.9, C.text1, 18, true, { h: 0.6, valign: "middle" }); lab(s, r[1], 3.2, y + 0.08, 6.1, C.text1, 14, false, { h: 0.65, valign: "middle" }); });
s.addNotes("Our rule is to follow the brain, not the GPU. Four things: senses that learn without labels; learning by counting, one example at a time; sleep, where the chip dreams old classes from small counters instead of storing examples; and sharing, because counts can simply be added together. There is no multiplier anywhere in the design.");

// 4 results staged
pres.addSection({ title: "Results" });
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Results" });
s.addText("It learns in stages and keeps what it knew", { placeholder: "title" });
s.addChart(pres.charts.BAR, [{ name: "SPARK Cortex", labels: ["digits", "clothing", "spoken words"], values: [95.8, 78.3, 82.9] }, { name: "Network (forgets)", labels: ["digits", "clothing", "spoken words"], values: [19.5, 20.0, 15.9] }], Object.assign(chartBase("Accuracy on all classes after 5 stages (%)"), { x: 0.5, y: 1.3, w: 5.8, h: 3.8, barDir: "col", barGrouping: "clustered", chartColors: ["5B6BD6", "D9534F"] }));
card(s, 6.5, 1.4, 3, 3.6);
lab(s, "SIMULATED", 6.7, 1.55, 2.6, C.accent2, 12, true);
lab(s, "Exact integer model of the chip, 5 seeds. The same arithmetic runs in the RTL, checked bit for bit.", 6.7, 1.9, 2.6, C.text1, 14, false, { h: 1.5 });
lab(s, "One class at a time (10 stages): 93.0 / 78.7 / 71.2 vs a network near 10.", 6.7, 3.5, 2.6, C.text1, 14, false, { h: 1.3 });
s.addNotes("Here is the core result. Learning five stages of two classes each, the chip keeps 95.8 percent on digits, 78.3 on clothing and 82.9 on spoken words, while a network that fine-tunes on each stage drops to roughly a fifth. This is simulated with the exact integer model, five seeds, and the RTL is bit-exact with it. Even one class at a time it holds 93, 79 and 71 percent in the earlier measurement.");

// 5 imprint
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Results" });
s.addText("A new class from one example, after shipping", { placeholder: "title" });
s.addChart(pres.charts.BAR, [{ name: "Before the fix", labels: ["digits", "clothing", "spoken words"], values: [54.1, 49.7, 45.2] }, { name: "With IMPRINT + short sleep", labels: ["digits", "clothing", "spoken words"], values: [69.9, 64.0, 48.3] }], Object.assign(chartBase("Accuracy on all 10 classes, 1 example per new class (%)"), { x: 0.5, y: 1.3, w: 5.8, h: 3.8, barDir: "col", barGrouping: "clustered", chartColors: ["8A93C9", "F2A93B"] }));
card(s, 6.5, 1.4, 3, 3.6);
lab(s, "SIMULATED, in RTL", 6.7, 1.55, 2.6, C.accent2, 12, true);
lab(s, "A novelty-gated imprint raises the table row for the new class at once, then a short sleep blends it in. Old classes stay within 1 to 5 points.", 6.7, 1.9, 2.6, C.text1, 14, false, { h: 2.0 });
lab(s, "Spoken words stay weak: we say so on the limits slide.", 6.7, 4.0, 2.6, C.accent4, 14, true, { h: 0.9 });
s.addNotes("We found a failure and redesigned for it: a brand-new class seen only once was almost invisible. The fix is called IMPRINT: when an example looks new, the chip writes its mean code into the table row immediately, then a short sleep of 300 dreams per known class blends it in. Digits go from 54 to 70, clothing 50 to 64, words only 45 to 48. It is implemented in the RTL and checked bit-exact.");

// 6 sound
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Results" });
s.addText("It hears: raw sound to word, on the chip", { placeholder: "title" });
s.addChart(pres.charts.BAR, [{ name: "Spoken words, trained clean", labels: ["clean", "20 dB", "10 dB", "5 dB"], values: [80.3, 72.4, 58.9, 47.1] }], Object.assign(chartBase("Accuracy with white noise added (%)"), { x: 0.5, y: 1.3, w: 5.2, h: 3.8, barDir: "col", chartColors: ["2FA37A"], showLegend: false }));
card(s, 5.9, 1.4, 3.6, 3.6);
lab(s, "SIMULATED, in RTL", 6.1, 1.55, 3.2, C.accent2, 12, true);
lab(s, "71.9 to 82.5 all at once", 6.1, 1.95, 3.2, C.text1, 22, true, { fontFace: "Cambria", h: 0.5 });
lab(s, "from word alignment: every word is shifted so its start lands at the same frame. Samples, cochlea, encoder and core run as one bit-exact chain.", 6.1, 2.55, 3.2, C.text1, 14, false, { h: 1.7 });
lab(s, "Needs 422 KB of memory for sound (PSRAM or an ASIC), so not on the Tang Nano yet.", 6.1, 4.2, 3.2, C.accent6, 12, false, { h: 0.7 });
s.addNotes("The sound path goes from raw samples through a cochlea, a noise-floor stage, the encoder and the learning core, all in RTL and bit-exact with the model. A word-alignment step that shifts each word so its start lands at the same frame lifted accuracy from 71.9 to 82.5 percent all at once, and the chip stays usable in noise: 72 percent at 20 dB, 59 at 10 dB. Sound needs 422 kilobytes of memory, which does not fit the small board.");

// 7 sharing
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Results" });
s.addText("Knowledge moves between chips", { placeholder: "title" });
s.addChart(pres.charts.BAR, [{ name: "Merge two chips", labels: ["digits", "clothing", "spoken words"], values: [93.3, 81.4, 64.3] }, { name: "Hand-over, then learn on", labels: ["digits", "clothing", "spoken words"], values: [95.6, 82.7, 71.6] }], Object.assign(chartBase("Accuracy after moving knowledge (%)"), { x: 0.5, y: 1.3, w: 5.8, h: 3.8, barDir: "col", barGrouping: "clustered", chartColors: ["8A93C9", "5B6BD6"] }));
card(s, 6.5, 1.4, 3, 3.6);
lab(s, "SIMULATED, 3 seeds", 6.7, 1.55, 2.6, C.accent2, 12, true);
lab(s, "Two chips trained on different classes merge by adding their counters. A board demo design reached 91.4% on all ten digits after one night (bit-exact design, PC-side emulator).", 6.7, 1.9, 2.6, C.text1, 14, false, { h: 2.8 });
s.addNotes("Because the memory is counts, two chips that learned different classes can be merged by adding their counters, or one chip can hand its memory to another that keeps learning. Merge gives 93, 81 and 64 percent; hand-over gives 96, 83 and 72. This is the weight-transfer story: no retraining on a server. The board demo reached 91.4 percent on all ten digits in the bit-exact emulator.");

// 7b diagnosis
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Results" });
s.addText("We found what limited the scores", { placeholder: "title" });
const dg = [["Not the senses", "A plain classifier trained on the chip's own code reaches 87.9% on clothing and 98.3% on digits. The code is good enough."], ["The readout", "The chip learns its table online in one pass with 5-bit entries, which loses 3 to 4 points."], ["The fix", "A slow second table averages the fast one: clothing 83.4 to 86.9, words 83.1 to 85.7, digits 97.0 to 97.6. Shifts and adds only; bit-exact in RTL; an ASIC option."], ["Next gain", "A finer detector grid for images: clothing 88.0, digits 98.3 all at once. It makes staged digits worse (93.2%), so it is an option."]];
dg.forEach((r, i) => { const y = 1.4 + i * 0.95; card(s, 0.5, y, 9, 0.82); s.addShape(pres.shapes.OVAL, { x: 0.65, y: y + 0.15, w: 0.5, h: 0.5, fill: { color: i === 2 ? C.accent3 : C.accent1 }, line: { color: i === 2 ? C.accent3 : C.accent1, width: 0 }, objectName: "marker" }); lab(s, String(i + 1), 0.65, y + 0.2, 0.5, C.text1, 18, true, { align: "center", h: 0.4 }); lab(s, r[0], 1.35, y + 0.08, 1.9, C.text1, 16, true, { h: 0.65, valign: "middle" }); lab(s, r[1], 3.2, y + 0.05, 6.1, C.text1, 13, false, { h: 0.72, valign: "middle" }); });
s.addNotes("We asked what actually limits the scores and tested it. A floating-point classifier trained on the chip's own code reaches 87.9 percent on clothing and 98.3 on digits, so the senses are not the limit. The chip's one-pass 5-bit readout is. A slow second table that follows the fast one fixes most of that: clothing 83.4 to 86.9, words 83 to 86, digits 97.0 to 97.6, with shifts and adds only, checked bit-exact in the RTL. A finer detector grid for images adds more, but it makes staged digits worse, so it stays an option. All simulated.");

// 8 cost
pres.addSection({ title: "Build" });
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Build" });
s.addText("Small, cheap, and no multiplier", { placeholder: "title" });
const kp = [["84 KB", "memory for images, 137x smaller than our first version", "design fact"], ["0", "hardware multipliers used on the $25 Tang Nano 20K (89% logic, 46/46 block RAM)", "SIMULATED, place and route"], ["~74x", "less energy per decision than an 8-bit network, counting the operations needed (9.4 nJ vs 696 nJ)", "ESTIMATED"], ["< 1 mm2", "SKY130 logic area; 18.8 mm2 with open SRAM macros", "ESTIMATED"]];
kp.forEach((k, i) => { const x = 0.5 + (i % 2) * 4.6, y = 1.3 + Math.floor(i / 2) * 1.85; card(s, x, y, 4.4, 1.7); lab(s, k[0], x + 0.2, y + 0.12, 4.0, C.accent2, 34, true, { fontFace: "Cambria", h: 0.7 }); lab(s, k[1], x + 0.2, y + 0.82, 4.0, C.text1, 13, false, { h: 0.55 }); lab(s, k[2], x + 0.2, y + 1.38, 4.0, C.accent6, 11, true, { h: 0.25 }); });
lab(s, "Say it carefully: the 74x is per operation needed. The SKY130 layout estimate is 0.18 to 0.26 uJ per decision, still 20 to 28x above the operation count.", 0.5, 4.95, 8.7, C.accent4, 12, false, { h: 0.45 });
s.addNotes("Cost. The image memory is 84 kilobytes. It fits a 25-dollar Tang Nano 20K with no hardware multipliers and timing met. Counting only the operations a decision needs, it uses about 74 times less energy than an 8-bit network, an estimate. I want to be careful: the layout estimate is higher, about a fifth of a microjoule per decision, so the honest wording is 74 times less per operation needed, not per chip.");

// 9 verified
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Build" });
s.addText("Verified bit for bit, and laid out", { placeholder: "title" });
card(s, 0.5, 1.4, 4.4, 3.5);
lab(s, "21 / 21", 0.7, 1.55, 4.0, C.accent3, 54, true, { fontFace: "Cambria", h: 1.0 });
lab(s, "RTL checks pass with 0 mismatches against the integer model: core, IMPRINT, slow table, encoder, finer-grid encoder, learning detectors, cochlea, sound chain, board top, host schedule.", 0.7, 2.75, 4.0, C.text1, 14, false, { h: 1.8 });
lab(s, "SIMULATED (RTL simulation)", 0.7, 4.45, 4.0, C.accent6, 11, true);
card(s, 5.1, 1.4, 4.4, 3.5);
lab(s, "1", 5.3, 1.55, 4.0, C.accent1, 54, true, { fontFace: "Cambria", h: 1.0 });
lab(s, "violation left in detailed routing of the SKY130 layout (from 174,309 on the first pass). The last one is a power-versus-signal short at a memory macro edge.", 5.3, 2.75, 4.0, C.text1, 14, false, { h: 1.8 });
lab(s, "ESTIMATED (open-source flow, no sign-off)", 5.3, 4.45, 4.0, C.accent6, 11, true);
s.addNotes("The design is not just a simulator result. Twenty-one bit-exact checks pass between the integer model and the RTL, covering the core, the few-shot fix, the sense layers, the whole sound chain and the board top. We also took it through an open-source SKY130 layout flow; detailed routing ended at one remaining violation at a memory macro edge. That is an estimate, with no sign-off and no fabrication.");

// 10 limits
pres.addSection({ title: "Honest" });
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Honest" });
s.addText("Where it is level, and where it is weaker", { placeholder: "title" });
s.addChart(pres.charts.BAR, [{ name: "SPARK Cortex (slow-table option)", labels: ["digits", "clothing", "spoken words"], values: [98.3, 87.9, 87.2] }, { name: "Network (MLP)", labels: ["digits", "clothing", "spoken words"], values: [97.8, 87.3, 85.5] }], Object.assign(chartBase("All at once, chip with LOOK AGAIN (%)"), { x: 0.5, y: 1.3, w: 4.6, h: 3.8, barDir: "col", barGrouping: "clustered", chartColors: ["5B6BD6", "6B7280"], valAxisMinVal: 50 }));
const lim = ["Level with a small network all at once, not better: a CNN reaches about 89 on clothing and 91 on words", "In stages clothing is 78 to 80%; digits 95%", "New spoken words from 1 to 5 recordings: only 12 to 29%", "Nothing measured on hardware yet; board run is next"];
s.addText(lim.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < lim.length - 1, paraSpaceAfter: 8 } })), { x: 5.3, y: 1.4, w: 4.2, h: 3.6, fontSize: 14, color: C.text1, valign: "top", isTextBox: true, margin: 0, fontFace: "Calibri" });
s.addNotes("This is the slide I want you to remember. Learning everything at once, with the slow-table option, the chip is level with a small network: 98.3 against 97.8 on digits, 87.9 against 87.3 on clothing, 87.2 against 85.5 on words, simulated, five seeds. Level, not better: a small convolutional network reaches about 89 on clothing and 91 on words. In stages clothing is 78 to 80 percent. New spoken words from one to five recordings are weak. We tried many fixes and recorded the failures, such as a second sensory layer, wider sound detectors and a shared prototype pool. And nothing is measured on hardware yet.");

// 11 prior art
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Honest" });
s.addText("Not the first, and clear about what is new", { placeholder: "title" });
card(s, 0.5, 1.4, 4.4, 3.5); card(s, 5.1, 1.4, 4.4, 3.5);
lab(s, "Already exists", 0.7, 1.55, 4.0, C.accent6, 20, true, { fontFace: "Cambria" });
s.addText([{ text: "Hyperdimensional-computing accelerators", options: { bullet: true, breakLine: true, paraSpaceAfter: 6 } }, { text: "Intel Loihi 2 (continual learning on spiking cores)", options: { bullet: true, breakLine: true, paraSpaceAfter: 6 } }, { text: "Replay-based continual learning", options: { bullet: true } }], { x: 0.7, y: 2.1, w: 4.0, h: 2.6, fontSize: 14, color: C.text1, valign: "top", isTextBox: true, margin: 0, fontFace: "Calibri" });
lab(s, "What we add", 5.3, 1.55, 4.0, C.accent2, 20, true, { fontFace: "Cambria" });
s.addText([{ text: "Dreams generated from 10-bit counters, no stored examples", options: { bullet: true, breakLine: true, paraSpaceAfter: 6 } }, { text: "A night that ends by itself", options: { bullet: true, breakLine: true, paraSpaceAfter: 6 } }, { text: "No multiplier, bit-exact from raw senses to decision", options: { bullet: true, breakLine: true, paraSpaceAfter: 6 } }, { text: "Ahead of HDC in our test after 5 stages: digits +2.2, sound +5.7", options: { bullet: true } }], { x: 5.3, y: 2.1, w: 4.0, h: 2.7, fontSize: 14, color: C.text1, valign: "top", isTextBox: true, margin: 0, fontFace: "Calibri" });
s.addNotes("We are not the first continual-learning chip. Hyperdimensional-computing accelerators and Intel's Loihi 2 exist. What is new is the combination: dreams generated from small counters so no examples are stored, a night that ends by itself, no multipliers, and a design that is bit-exact from raw senses to the decision. Against hyperdimensional computing in our own test, after five stages we are ahead on digits by 2.2 and on sound by 5.7 points, simulated.");

// 12 roadmap
pres.addSection({ title: "Next" });
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Next" });
s.addText("What comes next", { placeholder: "title" });
const steps = [["Done", "Model, RTL, 21 checks, slow-table option, FPGA fit, SKY130 layout estimate", C.accent3], ["Next", "First run on the real Tang Nano: the first MEASURED numbers", C.accent1], ["Then", "Learned word features, higher-fidelity dreams for clothing", C.accent2], ["Later", "Write-up, demo video, area and power estimates; no fabrication yet", C.accent5]];
steps.forEach((t, i) => { const x = 0.5 + i * 2.3; card(s, x, 1.5, 2.15, 2.9); s.addShape(pres.shapes.OVAL, { x: x + 0.15, y: 1.65, w: 0.55, h: 0.55, fill: { color: t[2] }, line: { color: t[2], width: 0 }, objectName: "marker" }); lab(s, String(i + 1), x + 0.15, 1.75, 0.55, C.text1, 18, true, { align: "center", h: 0.4 }); lab(s, t[0], x + 0.15, 2.35, 1.85, C.text1, 20, true, { fontFace: "Cambria", h: 0.4 }); lab(s, t[1], x + 0.15, 2.85, 1.85, C.text1, 13, false, { h: 1.5 }); });
lab(s, "Horizon: a provable result within 6 to 8 months, then shrink and attract investors.", 0.5, 4.6, 9, C.text1, 14, false, { h: 0.5 });
s.addNotes("What comes next. The model, RTL and layout estimate are done. The next milestone is the real board, which gives the first measured numbers. Then we work on the weak spots, learned word features and higher-fidelity dreams for clothing. The horizon is a provable result within six to eight months, with no fabrication yet.");

// 13 close
s = pres.addSlide({ masterName: "DARK", sectionTitle: "Next" });
s.addText("A chip that keeps learning", { placeholder: "title" });
lab(s, "It learns in the field, keeps what it knew, shares what it learned, and needs no multiplier. It is weaker than a network in some places, and we have said where.", 0.6, 3.1, 8.8, C.accent1, 18, false, { italic: true, h: 1.0 });
lab(s, "Thank you. Questions?", 0.6, 4.4, 8.8, C.background1, 22, true, { fontFace: "Cambria" });
s.addNotes("To close: SPARK Cortex is a chip that keeps learning after it ships. It keeps what it knew, shares what it learned, and needs no multiplier. It is weaker than a network in a few places, and I have told you where. Thank you, I am happy to take questions.");

pres.writeFile({ fileName: "SPARK_Cortex_pitch.pptx" }).then(() => applyTheme("SPARK_Cortex_pitch.pptx", THEME)).then(() => console.log("ok"));
