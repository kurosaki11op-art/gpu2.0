const pptxgen = require("pptxgenjs");
const { applyTheme } = require(process.env.SK + "/scripts/apply_theme.js");
const THEME = { name: "L", headFontFace: "Cambria", bodyFontFace: "Calibri",
  colors: { dk1: "151A3D", lt1: "FFFFFF", dk2: "2B3270", lt2: "EEF0FA", accent1: "F2A93B", accent2: "5B6BD6", accent3: "2FA37A", accent4: "D9534F", accent5: "8A93C9", accent6: "6B7280", hlink: "5B6BD6", folHlink: "8A93C9" } };
const pres = new pptxgen(); pres.layout = "LAYOUT_16x9"; pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "L"; pres.author = "L Lawliet (Navin), CKCET";
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

const notes = (s, t) => s.addNotes(t);
const bar = (s, series, title, opts) => s.addChart(pres.charts.BAR, series, Object.assign(chartBase(title), { barDir: "col", barGrouping: "clustered" }, opts));
const tag = (s, t, x, y, w, col) => lab(s, t, x, y, w, col || C.accent2, 12, true);

// 1 cover
pres.addSection({ title: "Open" });
let s = pres.addSlide({ masterName: "DARK", sectionTitle: "Open" });
s.addText("L", { placeholder: "title" });
lab(s, "A brain-principled chip that keeps learning after it ships", 0.6, 2.95, 8.8, C.accent1, 22, false, { italic: true, h: 0.5 });
lab(s, "L Lawliet  |  Navin (Kakashi), CKCET  |  PALS innoWAH! 2026-27", 0.6, 4.4, 8.8, C.accent5, 14);
lab(s, "Every number is labelled SIMULATED, ESTIMATED or MEASURED. The chip has not run on hardware yet: say it first, then show what is verified.", 0.6, 4.8, 8.8, C.accent5, 12);
notes(s, "Hello judges. We are L Lawliet from CKCET and the project is called L. L is a small chip design that keeps learning after it ships, without forgetting what it knew, with no multiplier, no matrices and no backpropagation. One promise before the numbers: every number on these slides is labelled simulated, estimated or measured, and nothing has run on a real board yet.");

// 2 problem
pres.addSection({ title: "Why" });
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Why" });
s.addText("AI stops learning the day it ships", { placeholder: "title" });
const stat = (x, big, small, col) => { card(s, x, 1.5, 2.8, 2.3); lab(s, big, x + 0.2, 1.7, 2.4, col, 54, true, { h: 1.0, fontFace: "Cambria" }); lab(s, small, x + 0.2, 2.85, 2.4, C.text1, 14, false, { h: 0.9 }); };
stat(0.5, "19.5%", "digits: a small CNN that learns in 5 stages keeps only the last stage", C.accent4);
stat(3.6, "20.0%", "clothing: same test, 60,000 images, same forgetting", C.accent4);
stat(6.7, "5.0%", "20 classes in 10 stages: almost everything is forgotten", C.accent4);
lab(s, "MEASURED: a CNN we trained on the same images, one seed. Fixing forgetting today means retraining from scratch: more energy, more heat, hardware thrown away when it can no longer be updated.", 0.5, 4.1, 9, C.text1, 15, false, { h: 1.0 });
notes(s, "A normal neural network learns once. Teach it in stages and it keeps only the last stage: about 20 percent on digits and clothing, and 5 percent on twenty classes. Those are measured numbers from a small CNN we trained on the same images, one seed. The usual fix is to retrain from scratch, which costs energy and means hardware cannot be updated in the field. A chip that learns in the field avoids that.");

// 3 idea
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Why" });
s.addText("The idea: a brain, as a chip", { placeholder: "title" });
const rows = [["Senses", "Eyes and ears turn pixels and sound into a sparse code. Detectors learn by themselves, no labels."], ["Learn by counting", "Each example is counted into a small fast table. No backpropagation, no multiplier, no matrices."], ["Dream and sleep", "Old classes are replayed from 10-bit counters, so nothing is stored. A slow table consolidates the fast one."], ["Look again", "When unsure, a second look at a finer code; when two senses disagree, trust the more confident one."], ["Share (optional)", "One chip works alone. Two chips can merge what they learned by adding counts, or one hands its memory to the other. A normal network cannot do this."]];
rows.forEach((r, i) => { const y = 1.25 + i * 0.77; card(s, 0.5, y, 9, 0.68); s.addShape(pres.shapes.OVAL, { x: 0.62, y: y + 0.1, w: 0.46, h: 0.46, fill: { color: C.accent1 }, line: { color: C.accent1, width: 0 }, objectName: "marker" }); lab(s, String(i + 1), 0.62, y + 0.16, 0.46, C.text1, 15, true, { align: "center", h: 0.3 }); lab(s, r[0], 1.25, y + 0.07, 2.2, C.text1, 15, true, { h: 0.5 }); lab(s, r[1], 3.4, y + 0.07, 5.9, C.text1, 12, false, { h: 0.55 }); });
notes(s, "Our rule is to follow the brain, not the GPU. Senses that learn without labels. Learning by counting, one example at a time, with no backpropagation, no multiplier and no matrices. Sleep: the chip dreams old classes from small counters instead of storing examples, and a slow table consolidates the fast one. Looking again when unsure, and trusting the more confident sense. And sharing: memory is counts, so chips can merge.");

// 4 staged
pres.addSection({ title: "Results" });
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Results" });
s.addText("It learns in stages and keeps what it knew", { placeholder: "title" });
bar(s, [{ name: "L chip design (no stored examples)", labels: ["digits", "clothing", "20 classes"], values: [95.6, 81.0, 87.4] }, { name: "CNN in stages (MEASURED)", labels: ["digits", "clothing", "20 classes"], values: [19.5, 20.0, 5.0] }], "Accuracy after learning in stages (%)", { x: 0.5, y: 1.3, w: 5.8, h: 3.8, chartColors: ["2FA37A", "8A93C9"] });
card(s, 6.5, 1.4, 3, 3.6);
tag(s, "SIMULATED (chip), MEASURED (CNN)", 6.7, 1.55, 2.6);
lab(s, "Exact integer model of the chip, 2-5 seeds, the full test sets. Digits and clothing: 60,000 training images in 5 stages of 2 classes. 20 classes: digits plus clothing in 10 stages.", 6.7, 1.95, 2.6, C.text1, 13, false, { h: 2.2 });
lab(s, "Stored examples: none. Memory: 84 KB for images.", 6.7, 4.2, 2.6, C.accent3, 13, true, { h: 0.7 });
notes(s, "This is the core result. Learning in stages of two classes with no stored examples, the chip keeps 95.6 percent on digits and 81 on clothing with sixty thousand training images, and 87.4 percent on twenty classes. The CNN that learned in the same stages keeps about 20 and 5 percent. The chip numbers are simulated with an exact integer model, two to five seeds; the CNN numbers are measured, one seed.");

// 5 close to a CNN
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Results" });
s.addText("Close to a CNN trained on everything", { placeholder: "title" });
bar(s, [{ name: "L chip design", labels: ["digits", "clothing", "20 classes", "35 words"], values: [98.45, 88.93, 91.18, 72.4] }, { name: "CNN, all data at once (MEASURED)", labels: ["digits", "clothing", "20 classes", "35 words"], values: [98.87, 90.96, 90.96, 72.5] }], "Accuracy (%)", { x: 0.5, y: 1.3, w: 6.0, h: 3.8, chartColors: ["2FA37A", "8A93C9"] });
card(s, 6.7, 1.4, 2.8, 3.6);
tag(s, "SIMULATED vs MEASURED", 6.9, 1.55, 2.4);
lab(s, "One pass with a second look on a finer code (digits, clothing: 60,000 images). 20 classes: one pass, no second look. Words: the chip learned in stages and the CNN all at once.", 6.9, 1.95, 2.4, C.text1, 12, false, { h: 2.3 });
lab(s, "A trained CNN is still ahead on clothing by 2 points.", 6.9, 4.3, 2.4, C.accent4, 12, true, { h: 0.6 });
notes(s, "With everything available at once, the chip with its second look is within half a point of a trained CNN on digits, two points behind on clothing, level on twenty classes, and level on thirty-five spoken words even though the chip learned the words in stages. The second look costs about 2.8 times the table memory. Say it plainly: a CNN is still ahead on clothing.");

// 6 scale
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Results" });
s.addText("It scales: more data does not break it", { placeholder: "title" });
bar(s, [{ name: "Fixed consolidation (first design)", labels: ["10,000", "30,000", "60,000"], values: [83.3, 79.4, 78.0] }, { name: "Consolidation scaled with the stage size", labels: ["10,000", "30,000", "60,000"], values: [83.3, 81.2, 81.0] }], "Clothing in stages, by training images (%)", { x: 0.5, y: 1.3, w: 5.8, h: 3.8, chartColors: ["8A93C9", "2FA37A"] });
card(s, 6.5, 1.4, 3, 3.6);
tag(s, "SIMULATED, 3 seeds", 6.7, 1.55, 2.6);
lab(s, "We tested 6x more data and found the staged result fell. One fixed rule fixed it: follow the slow table every max(100, stage size / 30) examples. Digits: 93.4 to 95.6 at 60,000 images.", 6.7, 1.95, 2.6, C.text1, 13, false, { h: 2.4 });
lab(s, "One pass barely improves with more data (clothing 86.6 to 87.6).", 6.7, 4.35, 2.6, C.accent6, 12, false, { h: 0.6 });
notes(s, "We tested whether the chip holds up with more data, and found a failure: at sixty thousand images the staged result fell. The cause was consolidation timing; one fixed rule that scales the follow interval with the stage size removes the collapse, on both datasets, without a per-dataset setting. We also report that one-pass accuracy barely improves with more data.");

// 7 hears
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Results" });
s.addText("It hears, and noise stops hurting as much", { placeholder: "title" });
bar(s, [{ name: "First design", labels: ["clean", "20 dB", "10 dB", "5 dB"], values: [68.3, 56.5, 39.8, 27.4] }, { name: "Noisy copies + second look", labels: ["clean", "20 dB", "10 dB", "5 dB"], values: [72.4, 67.3, 57.6, 47.2] }], "35 spoken words, learned in stages, white noise (%)", { x: 0.5, y: 1.3, w: 5.8, h: 3.8, chartColors: ["8A93C9", "2FA37A"] });
card(s, 6.5, 1.4, 3, 3.6);
tag(s, "SIMULATED, 3 seeds", 6.7, 1.55, 2.6);
lab(s, "Raw sound to word through an integer cochlea, noise floor, word alignment and the same counting table, bit-exact in RTL. Training also on one noisy copy of each clip adds no memory.", 6.7, 1.95, 2.6, C.text1, 13, false, { h: 2.4 });
lab(s, "Sound needs 422 KB: an ASIC or external memory, not the Tang Nano.", 6.7, 4.35, 2.6, C.accent6, 12, false, { h: 0.7 });
notes(s, "The sound path goes from raw samples through a cochlea and noise floor to the same counting table. With one noisy copy of each training clip and a second look, thirty-five words in stages reach 72.4 percent clean and 47 percent at 5 decibels, against 68 and 27 for the first design. The noise is simulated white noise, not real recordings.");

// 8 two senses
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Results" });
s.addText("Two senses help each other", { placeholder: "title" });
bar(s, [{ name: "Joint table", labels: ["clean", "picture 25% damaged", "picture 50% damaged"], values: [98.3, 97.5, 94.6] }, { name: "Weighted by confidence", labels: ["clean", "picture 25% damaged", "picture 50% damaged"], values: [98.9, 98.4, 96.2] }], "Digits: picture + sound (%)", { x: 0.5, y: 1.3, w: 5.8, h: 3.8, chartColors: ["8A93C9", "2FA37A"] });
card(s, 6.5, 1.4, 3, 3.6);
tag(s, "SIMULATED, 2-3 seeds", 6.7, 1.55, 2.6);
s.addText([{ text: "The ear names pictures with no picture labels: 93.9 after sleep cleaning", options: { bullet: true, breakLine: true, paraSpaceAfter: 5 } }, { text: "Groups form with no labels: 96.1 to 97.0 with 30 names", options: { bullet: true, breakLine: true, paraSpaceAfter: 5 } }, { text: "New classes noticed from inside: 99% of flagged pairs are new", options: { bullet: true } }], { x: 6.7, y: 1.95, w: 2.6, h: 2.6, fontSize: 12, color: C.text1, valign: "top", isTextBox: true, margin: 0, fontFace: "Calibri" });
lab(s, "Pictures and sounds are paired by class, not real recordings of one scene.", 6.7, 4.35, 2.6, C.accent4, 11, false, { h: 0.6 });
notes(s, "A retina and a cochlea feed one table. When a quarter of the picture is damaged, weighting each sense by how confident it is lifts digits from 97.5 to 98.4. A heard word can name pictures with no picture labels, groups can form with no labels, and the chip can notice a new class by itself. Be honest: the pictures and sounds come from different datasets that share only the digit.");

// 9 imprint
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Results" });
s.addText("A new class from one example, after shipping", { placeholder: "title" });
bar(s, [{ name: "Before the fix", labels: ["digits", "clothing", "spoken words"], values: [54.1, 49.7, 45.2] }, { name: "With IMPRINT + short sleep", labels: ["digits", "clothing", "spoken words"], values: [69.9, 64.0, 48.3] }], "Accuracy on all 10 classes, 1 example per new class (%)", { x: 0.5, y: 1.3, w: 5.8, h: 3.8, chartColors: ["8A93C9", "F2A93B"] });
card(s, 6.5, 1.4, 3, 3.6);
tag(s, "SIMULATED, in RTL", 6.7, 1.55, 2.6);
lab(s, "A novelty-gated imprint writes the new class into the table at once, then a short sleep blends it in. Old classes stay within 1 to 5 points.", 6.7, 1.95, 2.6, C.text1, 13, false, { h: 2.0 });
lab(s, "Spoken words from 1 to 5 recordings stay weak.", 6.7, 4.1, 2.6, C.accent4, 13, true, { h: 0.8 });
notes(s, "A brand-new class seen once was almost invisible. IMPRINT writes its mean code into the table at once and a short sleep blends it in: digits go from 54 to 70, clothing from 50 to 64. Spoken words from one to five recordings stay weak and I say so on the limits slide.");

// 10 sharing
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Results" });
s.addText("Two chips can share what they learned", { placeholder: "title" });
bar(s, [{ name: "Merge two chips", labels: ["digits", "clothing", "spoken words"], values: [93.3, 81.4, 64.3] }, { name: "Hand-over, then learn on", labels: ["digits", "clothing", "spoken words"], values: [95.6, 82.7, 71.6] }], "Accuracy after moving knowledge (%)", { x: 0.5, y: 1.3, w: 5.8, h: 3.8, chartColors: ["8A93C9", "2FA37A"] });
card(s, 6.5, 1.4, 3, 3.6);
tag(s, "SIMULATED, 3 seeds", 6.7, 1.55, 2.6);
lab(s, "One chip works alone; this is an option. Because memory is counts, two chips that learned different classes merge by adding counters, with no retraining. A trained network cannot merge this way. The board demo design reached 91.4% on all ten digits after one night (PC-side emulator).", 6.7, 1.95, 2.6, C.text1, 12, false, { h: 2.9 });
notes(s, "One chip works alone; sharing is an option. Because the memory is counts, two chips that learned different classes can be merged by adding their counters, or one chip hands its memory to another that keeps learning. Merge gives 93, 81 and 64 percent; hand-over gives 96, 83 and 72. A normal network cannot merge two separately trained copies like this. A GPU cluster joins many GPUs for size and speed, which is a different thing.");

// 11 cost
pres.addSection({ title: "Build" });
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Build" });
s.addText("Small, cheap, and no multiplier", { placeholder: "title" });
const kp = [["84 KB", "memory for images (second look: about 2.8x)", "design fact"], ["0", "hardware multipliers on the $25 Tang Nano 20K (89% logic, 46/46 block RAM)", "SIMULATED, place and route"], ["~74x", "less energy per decision than an 8-bit network, counting the operations needed (9.4 nJ vs 696 nJ)", "ESTIMATED"], ["422 KB", "sound memory: needs external memory or an ASIC", "design fact"]];
kp.forEach((k, i) => { const x = 0.5 + (i % 2) * 4.6, y = 1.3 + Math.floor(i / 2) * 1.85; card(s, x, y, 4.4, 1.7); lab(s, k[0], x + 0.2, y + 0.12, 4.0, C.accent2, 34, true, { fontFace: "Cambria", h: 0.7 }); lab(s, k[1], x + 0.2, y + 0.82, 4.0, C.text1, 13, false, { h: 0.55 }); lab(s, k[2], x + 0.2, y + 1.38, 4.0, C.accent6, 11, true); });
lab(s, "Say it carefully: the 74x is per operation needed. The SKY130 layout estimate is 0.18 to 0.26 uJ per decision, 20 to 28x above the operation count.", 0.5, 4.95, 8.7, C.accent4, 12, false, { h: 0.45 });
notes(s, "Cost. The image memory is 84 kilobytes and fits a 25-dollar Tang Nano 20K with no hardware multipliers. Counting only the operations a decision needs it uses about 74 times less energy than an 8-bit network, an estimate. The layout estimate is higher, about a fifth of a microjoule. The second look costs about 2.8 times the table memory, and sound needs 422 kilobytes.");

// 12 verified
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Build" });
s.addText("Verified bit for bit, and laid out", { placeholder: "title" });
card(s, 0.5, 1.4, 4.4, 3.5);
lab(s, "REGRESSION_COUNT", 0.7, 1.55, 4.0, C.accent3, 54, true, { fontFace: "Cambria", h: 1.0 });
lab(s, "RTL checks, 0 mismatches against the integer model: core, tail memory, IMPRINT, slow table, encoders, cochlea, sound chain, two-sense chip, cue weighting, second look, threshold and novelty units, clustering, board top, host schedule.", 0.7, 2.75, 4.0, C.text1, 12, false, { h: 1.9 });
lab(s, "SIMULATED (RTL simulation)", 0.7, 4.5, 4.0, C.accent6, 11, true);
card(s, 5.1, 1.4, 4.4, 3.5);
lab(s, "1", 5.3, 1.55, 4.0, C.accent1, 54, true, { fontFace: "Cambria", h: 1.0 });
lab(s, "violation left in detailed routing of the SKY130 layout (from 174,309 on the first pass), a power-versus-signal short at a memory macro edge.", 5.3, 2.75, 4.0, C.text1, 13, false, { h: 1.8 });
lab(s, "ESTIMATED (open-source flow, no sign-off)", 5.3, 4.5, 4.0, C.accent6, 11, true);
notes(s, "The design is not just a simulator result. Every check passes bit for bit between the integer model and the RTL, covering the learning core, the sense layers, the whole sound chain, the two-sense chip, the new units that moved host steps onto the chip, and the board top. We also took it through an open-source SKY130 layout flow; routing ended at one remaining violation. This is verification in simulation, not a chip.");

// 13a what it solves
pres.addSection({ title: "Honest" });
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Honest" });
s.addText("What L solves, and what it does not", { placeholder: "title" });
card(s, 0.5, 1.4, 4.4, 3.6); card(s, 5.1, 1.4, 4.4, 3.6);
lab(s, "What L solves", 0.7, 1.55, 4.0, C.accent3, 20, true, { fontFace: "Cambria" });
s.addText([{ text: "Small AI on devices that must keep learning: no retraining on a server, no hardware thrown away to update it (SIMULATED)", options: { bullet: true, breakLine: true, paraSpaceAfter: 6 } }, { text: "No stored examples, 84 KB of memory for images, no multiplier", options: { bullet: true, breakLine: true, paraSpaceAfter: 6 } }, { text: "About 74x less energy per decision than an 8-bit network, counting operations needed (ESTIMATED)", options: { bullet: true } }], { x: 0.7, y: 2.05, w: 4.0, h: 2.8, fontSize: 13, color: C.text1, valign: "top", isTextBox: true, margin: 0, fontFace: "Calibri" });
lab(s, "What L does not solve", 5.3, 1.55, 4.0, C.accent4, 20, true, { fontFace: "Cambria" });
s.addText([{ text: "The cost of large language models and image generators: GPU and memory prices, data-centre heat and water", options: { bullet: true, breakLine: true, paraSpaceAfter: 6 } }, { text: "It cannot run existing models (CNNs, transformers, LLMs): it is a dedicated chip for its own brain-style model", options: { bullet: true, breakLine: true, paraSpaceAfter: 6 } }, { text: "Nothing is measured on hardware yet", options: { bullet: true } }], { x: 5.3, y: 2.05, w: 4.0, h: 2.8, fontSize: 13, color: C.text1, valign: "top", isTextBox: true, margin: 0, fontFace: "Calibri" });
notes(s, "Be clear about scope. L solves a small part of the AI problem: devices that must keep learning in the field without retraining on a server and without being thrown away. That is simulated, and the energy figure is an estimate. L does not solve what is driving GPU and memory prices today, which is large language models and image generators in data centres. It also cannot run existing models: it is a dedicated chip for its own model. And nothing is measured on hardware yet.");

// 13 limits
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Honest" });
s.addText("Where it is level, and where it is weaker", { placeholder: "title" });
const lim = ["Nothing is measured on hardware yet: every chip number is simulated", "Staged clothing about 82%, 5 points below its one pass; many ideas tried", "A trained CNN is ahead by about 2 points on clothing when all data is available", "Small tests: digits, clothing, 20 classes, up to 35 words; noise is simulated; two-sense data is paired by class", "Second look costs about 2.8x memory; a few steps still run on the host"];
s.addText(lim.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < lim.length - 1, paraSpaceAfter: 9 } })), { x: 0.5, y: 1.4, w: 9, h: 3.6, fontSize: 16, color: C.text1, valign: "top", isTextBox: true, margin: 0, fontFace: "Calibri" });
notes(s, "This is the slide I want you to remember. Nothing has run on hardware. Staged clothing is about 82 percent, five points under its one-pass number, and I tried many fixes. A trained CNN is still ahead on clothing by about two points. The tests are small and the noise is simulated; the two-sense data is paired by class, not real audio-visual recordings. The second look costs about 2.8 times the memory, and a few steps still run on the host.");

// 14 prior art
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Honest" });
s.addText("Not the first, and clear about what is new", { placeholder: "title" });
card(s, 0.5, 1.4, 4.4, 3.5); card(s, 5.1, 1.4, 4.4, 3.5);
lab(s, "Already exists", 0.7, 1.55, 4.0, C.accent6, 20, true, { fontFace: "Cambria" });
s.addText([{ text: "Hyperdimensional-computing accelerators", options: { bullet: true, breakLine: true, paraSpaceAfter: 6 } }, { text: "Intel Loihi 2, TrueNorth, SpiNNaker (event-driven spiking chips)", options: { bullet: true, breakLine: true, paraSpaceAfter: 6 } }, { text: "Replay-based continual learning", options: { bullet: true } }], { x: 0.7, y: 2.1, w: 4.0, h: 2.6, fontSize: 15, color: C.text1, valign: "top", isTextBox: true, margin: 0, fontFace: "Calibri" });
lab(s, "What we add", 5.3, 1.55, 4.0, C.accent2, 20, true, { fontFace: "Cambria" });
s.addText([{ text: "Dreams from 10-bit counters, no stored examples", options: { bullet: true, breakLine: true, paraSpaceAfter: 6 } }, { text: "A night that ends by itself; consolidation that scales with the data", options: { bullet: true, breakLine: true, paraSpaceAfter: 6 } }, { text: "No multiplier or matrix, bit-exact from raw senses to decision, with grouping and thresholds on the chip", options: { bullet: true } }], { x: 5.3, y: 2.1, w: 4.0, h: 2.6, fontSize: 14, color: C.text1, valign: "top", isTextBox: true, margin: 0, fontFace: "Calibri" });
notes(s, "We are not the first continual-learning chip. Hyperdimensional-computing accelerators and event-driven spiking chips such as Loihi 2, TrueNorth and SpiNNaker exist. What we add is the combination: dreams from small counters so no examples are stored, a night that ends by itself, consolidation that scales with the data, and a design with no multiplier or matrix that is bit-exact from raw senses to the decision.");

// 15 roadmap
pres.addSection({ title: "Next" });
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Next" });
s.addText("What comes next", { placeholder: "title" });
const steps = [["Done", "Model, RTL with every check passing, second look, tail memory, on-chip thresholds and grouping, scale tests", C.accent3], ["Next", "Run on the real Tang Nano: the first MEASURED numbers", C.accent1], ["Then", "Harder tests: larger vocabulary, real recorded noise, a harder image set", C.accent2], ["Later", "Matrix-free chip for the L language model; ASIC memory for sound and the second look", C.accent5]];
steps.forEach((t, i) => { const x = 0.5 + i * 2.3; card(s, x, 1.5, 2.15, 2.9); s.addShape(pres.shapes.OVAL, { x: x + 0.15, y: 1.65, w: 0.55, h: 0.55, fill: { color: t[2] }, line: { color: t[2], width: 0 }, objectName: "marker" }); lab(s, String(i + 1), x + 0.15, 1.75, 0.55, C.text1, 18, true, { align: "center", h: 0.4 }); lab(s, t[0], x + 0.15, 2.35, 1.9, C.text1, 17, true, { fontFace: "Cambria" }); lab(s, t[1], x + 0.15, 2.8, 1.9, C.text1, 11, false, { h: 1.5 }); });
lab(s, "Horizon: a provable result within 6 to 8 months, then shrink and attract investors. No fabrication is planned yet.", 0.5, 4.6, 9, C.text1, 14, false, { h: 0.5 });
notes(s, "What comes next. The model and RTL are done and verified in simulation. The next milestone is the real Tang Nano board, which gives the first measured numbers. Then harder tests: a larger vocabulary, real recorded noise and a harder image set. Later, a matrix-free chip for the L language model, and external memory for sound and the second look. No fabrication is planned yet.");

// 15b two tracks
s = pres.addSlide({ masterName: "LIGHT", sectionTitle: "Next" });
s.addText("Two tracks toward the bigger problem", { placeholder: "title" });
card(s, 0.5, 1.4, 4.4, 3.6); card(s, 5.1, 1.4, 4.4, 3.6);
lab(s, "Track 1: the L chip (hardware)", 0.7, 1.52, 4.0, C.accent3, 17, true, { fontFace: "Cambria" });
s.addText([{ text: "Now: verified in simulation, bit-exact RTL", options: { bullet: true, breakLine: true, paraSpaceAfter: 5 } }, { text: "Next: run on the Tang Nano for the first MEASURED numbers", options: { bullet: true, breakLine: true, paraSpaceAfter: 5 } }, { text: "Then: harder tests, external memory for sound and the second look", options: { bullet: true } }], { x: 0.7, y: 2.0, w: 4.0, h: 2.9, fontSize: 13, color: C.text1, valign: "top", isTextBox: true, margin: 0, fontFace: "Calibri" });
lab(s, "Track 2: the L AI model (later)", 5.3, 1.52, 4.0, C.accent2, 17, true, { fontFace: "Cambria" });
s.addText([{ text: "Gate 1: measure the model: firing rates, ablations, seeds", options: { bullet: true, breakLine: true, paraSpaceAfter: 4 } }, { text: "Gate 2: fused GPU baseline; stop if a GPU is already close", options: { bullet: true, breakLine: true, paraSpaceAfter: 4 } }, { text: "Gate 3: matrix-free version keeps its quality", options: { bullet: true, breakLine: true, paraSpaceAfter: 4 } }, { text: "Then: simulator and FPGA; study memory: can constant-size state and event-driven reads move work from scarce HBM to cheaper DRAM or SRAM? (a question, not a claim)", options: { bullet: true } }], { x: 5.3, y: 2.0, w: 4.0, h: 2.9, fontSize: 12, color: C.text1, valign: "top", isTextBox: true, margin: 0, fontFace: "Calibri" });
lab(s, "PLAN: the language-model track has small-scale evidence only (9M parameters).", 0.5, 5.05, 9, C.accent6, 11, false, { h: 0.3 });
notes(s, "We plan to approach the bigger problem on two tracks. Track one is the L chip, which is done in simulation and next goes to a real board. Track two is the L AI model for language, which has small-scale evidence only, so it goes through gates: first measure the model, then compare against a fused GPU implementation and stop if the GPU is already close, then check that a matrix-free version keeps its quality. Only then a simulator and an FPGA. Later we study memory: whether the constant-size state and event-driven reads can move work from scarce high-bandwidth memory to cheaper DRAM or on-chip memory. That is a question to study, not a claim.");

// 16 close
s = pres.addSlide({ masterName: "DARK", sectionTitle: "Next" });
s.addText("A chip that keeps learning", { placeholder: "title" });
lab(s, "It learns in the field, keeps what it knew, shares what it learned, and needs no multiplier. It is weaker than a trained network in some places, and we have said where.", 0.6, 3.1, 8.8, C.accent1, 18, false, { italic: true, h: 1.0 });
lab(s, "Thank you. Questions?", 0.6, 4.4, 8.8, C.background1, 22, true, { fontFace: "Cambria" });
notes(s, "To close: L is a chip design that keeps learning after it ships. It keeps what it knew, shares what it learned, and needs no multiplier. It is weaker than a trained network in a few places, and I have told you where. Thank you, I am happy to take questions.");

pres.writeFile({ fileName: "L_pitch.pptx" }).then(() => applyTheme("L_pitch.pptx", THEME)).then(() => console.log("ok"));
