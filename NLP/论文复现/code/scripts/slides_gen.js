// 生成论文复现汇报 slides.pptx（7 页，16:9，G17/P33）
// 运行：node slides_gen.js  （输出到 论文复现/slides.pptx）
const pptxgen = require("pptxgenjs");
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5 in

const FIG = "D:/code/Git_Local/project/NLP/论文复现/材料/figures";
const OUT = "D:/code/Git_Local/project/NLP/论文复现/slides.pptx";

// 配色（与图件同源的蓝色系）
const C = {
  dark: "083B63",      // 深蓝（首尾页背景）
  primary: "0B6FB8",   // 主蓝（与图 accent 一致）
  deep: "0A4C85",      // 标题深蓝
  tint: "EFF6FB",      // 卡片浅蓝底
  tint2: "D9EBF7",     // 强调卡片底
  light: "79C4FE",     // 亮蓝（与图 primary 一致）
  iceOnDark: "BCD9F0", // 深底上的浅字
  red: "C0392B",
  redTint: "FBEDEC",
  greenOnDark: "9AD9A6",
  redOnDark: "F2A9A0",
  gray: "5B6B7A",
};
const FONT = "Microsoft YaHei";

function title(slide, text) {
  slide.addText(text, { x: 0.55, y: 0.32, w: 12.2, h: 0.62, fontFace: FONT,
    fontSize: 30, bold: true, color: C.deep, margin: 0 });
}
function card(slide, opts) {
  slide.addShape(pres.ShapeType.roundRect, Object.assign({ rectRadius: 0.08,
    fill: { color: C.tint }, line: { type: "none" } }, opts));
}

// ============ S1 题目和范围（深底） ============
{
  const s = pres.addSlide();
  s.background = { color: C.dark };
  s.addText("论文复现：Calibrate Before Use", { x: 0.8, y: 1.15, w: 11.7, h: 0.95,
    fontFace: FONT, fontSize: 40, bold: true, color: "FFFFFF", align: "center", margin: 0 });
  s.addText("Improving Few-Shot Performance of Language Models（Zhao et al., ICML 2021）",
    { x: 0.8, y: 2.12, w: 11.7, h: 0.45, fontFace: FONT, fontSize: 20, italic: true,
      color: C.iceOnDark, align: "center", margin: 0 });
  s.addText("组号 G17   ·   论文号 P33", { x: 0.8, y: 2.62, w: 11.7, h: 0.42,
    fontFace: FONT, fontSize: 20, color: C.light, align: "center", margin: 0 });
  card(s, { x: 0.9, y: 3.35, w: 11.53, h: 1.85, fill: { color: "FFFFFF", transparency: 90 } });
  s.addText([
    { text: "复现范围（缩规模部分复现）", options: { fontSize: 21, bold: true, color: "FFFFFF", breakLine: true } },
    { text: "本地 GPT-2 四规格（124M / 355M / 774M / 1.5B）× SST-2 / AGNews / TREC × shots 0/1/4/8 × 5 seeds，fp32",
      options: { fontSize: 20, color: C.iceOnDark, breakLine: true } },
    { text: "主实验 gpt2-xl（1.5B）直接对应论文 Table 4；其余三档为本组自扩的规模扫描",
      options: { fontSize: 20, color: C.iceOnDark } },
  ], { x: 1.15, y: 3.5, w: 11.0, h: 1.6, fontFace: FONT, align: "left", margin: 0, paraSpaceAfter: 6 });
  const chips = ["Table 4：校准提升准确率、降方差", "Figure 1：方差随 shot 变化", "Table 3：内容无关输入的选择"];
  chips.forEach((t, i) => {
    const x = 0.9 + i * 3.92;
    card(s, { x, y: 5.55, w: 3.7, h: 0.95, fill: { color: C.primary, transparency: 25 } });
    s.addText(t, { x, y: 5.55, w: 3.7, h: 0.95, fontFace: FONT, fontSize: 18,
      color: "FFFFFF", align: "center", valign: "middle", margin: 0.05 });
  });
  s.addText("全部 240 run 为本机真实运行 · 每个数字可溯源到 results/ 下的文件",
    { x: 0.8, y: 6.9, w: 11.7, h: 0.4, fontFace: FONT, fontSize: 14, color: C.iceOnDark,
      align: "center", margin: 0 });
  s.addNotes("开场 30 秒：论文与目标（Table 4 主目标 + Figure 1 + Table 3）；强调缩规模范围与 240 run 全部真实运行。");
}

// ============ S2 问题 ============
{
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  title(s, "问题：少样本预测被「答案先验」带偏");
  s.addText([
    { text: "现象：把输入换成内容无关的 “N/A”，模型仍以高概率预测某个固定类", options: { bullet: true, breakLine: true } },
    { text: "后果：先验与样本真实类别冲突时，逐词概率的 argmax 被系统性带偏", options: { bullet: true, breakLine: true } },
    { text: "原文主张：该先验可以被探测并抵消 —— 上下文校准（contextual calibration）", options: { bullet: true } },
  ], { x: 0.55, y: 1.35, w: 6.4, h: 4.0, fontFace: FONT, fontSize: 20, color: "1F2A36",
      align: "left", margin: 0, paraSpaceAfter: 14, valign: "top" });
  // 右侧示意：内容无关输入下的答案先验
  card(s, { x: 7.3, y: 1.35, w: 5.45, h: 4.0, fill: { color: C.tint } });
  s.addText("内容无关输入下的答案先验（示意）", { x: 7.55, y: 1.55, w: 4.95, h: 0.4,
    fontFace: FONT, fontSize: 18, bold: true, color: C.deep, margin: 0 });
  const bars = [["World", 0.46, "46%"], ["Sports", 0.27, "27%"], ["Business", 0.18, "18%"], ["Sci/Tech", 0.09, "9%"]];
  bars.forEach(([lab, w, pct], i) => {
    const y = 2.15 + i * 0.78;
    s.addText(lab, { x: 7.55, y, w: 1.15, h: 0.5, fontFace: FONT, fontSize: 18,
      color: "1F2A36", margin: 0, valign: "middle" });
    s.addShape(pres.ShapeType.rect, { x: 8.75, y: y + 0.05, w: 3.1 * w, h: 0.4,
      fill: { color: i === 0 ? C.primary : C.light }, line: { type: "none" } });
    s.addText(pct, { x: 8.85 + 3.1 * w, y, w: 0.8, h: 0.5, fontFace: FONT, fontSize: 18,
      color: C.gray, margin: 0, valign: "middle" });
  });
  card(s, { x: 0.55, y: 5.75, w: 12.2, h: 1.15, fill: { color: C.tint2 } });
  s.addText([
    { text: "校准：探测先验 p_cf，令 W = diag(1/p_cf)，预测改为 argmax(W·p̂)；直觉 = 按先验的倒数重加权，抵消偏置",
      options: { fontSize: 22, bold: true, color: C.deep } },
  ], { x: 0.85, y: 5.75, w: 11.7, h: 1.15, fontFace: FONT, align: "center", valign: "middle", margin: 0 });
  s.addNotes("用示意条说明先验 ≠ 均匀；校准的直觉是按先验倒数重加权。");
}

// ============ S3 方法 ============
{
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  title(s, "方法：基线 greedy → 上下文校准");
  const rows = [
    ["1", "基线（greedy）", "prompt ＋ few-shot 训练样例 → 标签词首 token 概率（top-100，缺失回声补全）→ argmax"],
    ["2", "探测先验 p_cf", "用 N/A / 空串 / [MASK] 三种内容无关输入替换测试句，答案分布取平均并归一化"],
    ["3", "校准预测", "W = diag(1/p_cf) 对每类概率重加权后取 argmax（b = 0）"],
  ];
  rows.forEach(([n, h, body], i) => {
    const y = 1.3 + i * 1.85;
    card(s, { x: 0.55, y, w: 7.55, h: 1.62 });
    s.addShape(pres.ShapeType.ellipse, { x: 0.85, y: y + 0.5, w: 0.62, h: 0.62,
      fill: { color: C.primary }, line: { type: "none" } });
    s.addText(n, { x: 0.85, y: y + 0.5, w: 0.62, h: 0.62, fontFace: FONT, fontSize: 24,
      bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0 });
    s.addText([
      { text: h, options: { fontSize: 21, bold: true, color: C.deep, breakLine: true } },
      { text: body, options: { fontSize: 20, color: "1F2A36" } },
    ], { x: 1.7, y: y + 0.12, w: 6.25, h: 1.4, fontFace: FONT, margin: 0, paraSpaceAfter: 4 });
  });
  card(s, { x: 8.35, y: 1.3, w: 4.43, h: 5.4, fill: { color: C.tint2 } });
  s.addText([
    { text: "工程对齐（与作者代码）", options: { fontSize: 21, bold: true, color: C.deep, breakLine: true } },
    { text: "prompt 格式与标签词逐字一致", options: { bullet: true, breakLine: true } },
    { text: "抽样 / 回声补全 / 校准逻辑与作者 master 同源", options: { bullet: true, breakLine: true } },
    { text: "9 项实现差异逐条声明（code/README §6）", options: { bullet: true, breakLine: true } },
    { text: "重跑同配置自动跳过并核验配置指纹，防静默复用", options: { bullet: true } },
  ], { x: 8.6, y: 1.5, w: 3.95, h: 5.0, fontFace: FONT, fontSize: 20, color: "1F2A36",
      margin: 0, paraSpaceAfter: 10, valign: "top" });
  s.addNotes("三步讲清方法；右侧强调与作者代码的对齐与差异声明（评分点：实现来源说明）。");
}

// ============ S4 设置 ============
{
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  title(s, "实验设置：全网格 240 run");
  const stats = [
    ["240", "run 全部落盘，一次通过零重试"],
    ["1h40m", "全网格 fp32 总耗时"],
    ["5×4", "seeds × shots 0/1/4/8"],
    ["300", "冻结测试子集 seed 0"],
  ];
  stats.forEach(([big, lab], i) => {
    const x = 0.55 + i * 3.12;
    card(s, { x, y: 1.3, w: 2.92, h: 1.75 });
    s.addText(big, { x, y: 1.42, w: 2.92, h: 0.85, fontFace: FONT, fontSize: 44, bold: true,
      color: C.primary, align: "center", margin: 0 });
    s.addText(lab, { x: x + 0.12, y: 2.3, w: 2.68, h: 0.68, fontFace: FONT, fontSize: 16,
      color: C.gray, align: "center", margin: 0 });
  });
  card(s, { x: 0.55, y: 3.45, w: 6.05, h: 3.5 });
  s.addText([
    { text: "网格与环境", options: { fontSize: 21, bold: true, color: C.deep, breakLine: true } },
    { text: "4 模型：124M / 355M / 774M / 1.5B（主实验 XL ↔ Table 4）", options: { bullet: true, breakLine: true } },
    { text: "3 数据集：SST-2（2 类）/ AGNews（4 类）/ TREC（6 类）", options: { bullet: true, breakLine: true } },
    { text: "Python 3.11 · torch 2.14 cu126 · transformers 5.22", options: { bullet: true, breakLine: true } },
    { text: "RTX 4060 Laptop 8GB，纯推理无训练", options: { bullet: true } },
  ], { x: 0.8, y: 3.65, w: 5.6, h: 3.1, fontFace: FONT, fontSize: 20, color: "1F2A36",
      margin: 0, paraSpaceAfter: 10, valign: "top" });
  card(s, { x: 6.85, y: 3.45, w: 5.93, h: 3.5 });
  s.addText([
    { text: "批大小按（模型×数据集）显存探针核定", options: { fontSize: 21, bold: true, color: C.deep, breakLine: true } },
    { text: "gpt2 16/16/16 · medium 16/8/16", options: { bullet: true, breakLine: true } },
    { text: "large 12/4/12 · xl 2/2/2（agnews 长文本降档）", options: { bullet: true, breakLine: true } },
    { text: "XL fp32 超物理显存：WDDM 溢出兜底，bs=2 实测最快，全程无 OOM", options: { bullet: true, breakLine: true } },
    { text: "单数据集失败同 bs 自动重试（240 run 实际零重试）", options: { bullet: true } },
  ], { x: 7.1, y: 3.65, w: 5.45, h: 3.1, fontFace: FONT, fontSize: 20, color: "1F2A36",
      margin: 0, paraSpaceAfter: 10, valign: "top" });
  s.addNotes("设置页给数字证据：240/1h40m/5seeds/300 子集；bs 探针与 XL 溢出是工程亮点。");
}

// ============ S5 结果 ============
{
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  title(s, "主要结果：规模依赖 · TREC 例外 · 方差");
  const th = { fontFace: FONT, fontSize: 18, color: "FFFFFF", bold: true, fill: { color: C.primary }, align: "center", valign: "middle" };
  const td = (t, color) => ({ text: t, options: { fontFace: FONT, fontSize: 18, bold: true,
    color, align: "center", valign: "middle", fill: { color: "FFFFFF" } } });
  const rows = [
    [{ text: "0-shot Δ", options: Object.assign({}, th, { align: "left" }) },
     { text: "SST-2", options: Object.assign({}, th) }, { text: "AGNews", options: Object.assign({}, th) },
     { text: "TREC", options: Object.assign({}, th) }],
    [td("gpt2 (124M)", "1F2A36"), td("−12.0", C.red), td("−5.0", C.red), td("−14.3", C.red)],
    [td("gpt2-medium", "1F2A36"), td("+17.3", C.primary), td("+23.0", C.primary), td("−24.7", C.red)],
    [td("gpt2-large", "1F2A36"), td("+13.3", C.primary), td("+16.7", C.primary), td("−18.7", C.red)],
    [td("gpt2-xl", "1F2A36"), td("+16.0", C.primary), td("+11.0", C.primary), td("−7.7", C.red)],
  ];
  s.addTable(rows, { x: 0.55, y: 1.3, w: 7.15, colW: [2.05, 1.7, 1.7, 1.7], rowH: 0.52,
    border: { pt: 1, color: "D7E4EF" } });
  s.addText("校准 − 基线（百分点）；0-shot 无训练样例，无 seed 方差", { x: 0.55, y: 4.05, w: 7.15, h: 0.35,
    fontFace: FONT, fontSize: 14, color: C.gray, margin: 0 });
  s.addText([
    { text: "① SST-2 / AGNews 0-shot：≥355M 全面正收益（+11~+23pp），124M 反向 —— 校准收益呈规模依赖", options: { breakLine: true } },
    { text: "② TREC 四模型全负（medium 校准后 0.0267，低于随机 0.167）；论文 Table 4 报告 XL 全 shot +13~21pp —— 本组如实报告不一致", options: { breakLine: true } },
    { text: "③ 降方差未复现：36 个 few-shot 配置中 26 个升方差（std 比值中位 1.33）", options: {} },
  ], { x: 0.55, y: 4.55, w: 7.15, h: 2.6, fontFace: FONT, fontSize: 20, color: "1F2A36",
      margin: 0, paraSpaceAfter: 12, valign: "top" });
  s.addImage({ path: FIG + "/fig3_fullgrid_acc.png", x: 8.0, y: 1.15, w: 4.85, h: 5.97 });
  s.addNotes("先表后图：0-shot 决定性（无方差）；指 fig3 讲 1-shot 高方差来源（先验坍缩方向随集合变化）。");
}

// ============ S6 消融与案例 ============
{
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  title(s, "消融（Table 3）与案例分析");
  s.addImage({ path: FIG + "/fig4_table3_ablation.png", x: 0.55, y: 1.25, w: 7.4, h: 2.96 });
  s.addText("四种内容无关输入选择 × 4 模型（左：SST-2 1-shot；右：AGNews 0-shot）",
    { x: 0.55, y: 4.24, w: 7.4, h: 0.34, fontFace: FONT, fontSize: 14, color: C.gray, margin: 0 });
  card(s, { x: 0.55, y: 4.72, w: 7.4, h: 2.2 });
  s.addText([
    { text: "Table 3 结论复现成立", options: { fontSize: 21, bold: true, color: C.deep, breakLine: true } },
    { text: "选择有实质影响：XL AGNews 0-shot 空串 0.5733 vs 三者平均 0.5200（5.3pp）", options: { bullet: true, breakLine: true } },
    { text: "单输入普遍不劣于三者平均 —— 存在多种好选择", options: { bullet: true, breakLine: true } },
    { text: "四值全同的组 = 校准坍缩：argmax 对 p_cf 不敏感", options: { bullet: true } },
  ], { x: 0.8, y: 4.86, w: 6.95, h: 1.95, fontFace: FONT, fontSize: 20, color: "1F2A36",
      margin: 0, paraSpaceAfter: 8, valign: "top" });
  card(s, { x: 8.2, y: 1.25, w: 4.58, h: 2.72, fill: { color: "EAF6EA" } });
  s.addText([
    { text: "案例 · 修复（AGNews 1-shot）", options: { fontSize: 20, bold: true, color: "1E7B34", breakLine: true } },
    { text: "基线 Sports 0.496 vs Business 0.499，差 0.3pp 判错；校准抑制 Business 先验 → Sports 分数 443 : 9.2 强势翻正", options: { fontSize: 20, color: "1F2A36" } },
  ], { x: 8.42, y: 1.4, w: 4.14, h: 2.45, fontFace: FONT, margin: 0, paraSpaceAfter: 6 });
  card(s, { x: 8.2, y: 4.2, w: 4.58, h: 2.72, fill: { color: C.redTint } });
  s.addText([
    { text: "案例 · 破坏（TREC 1-shot）", options: { fontSize: 20, bold: true, color: C.red, breakLine: true } },
    { text: "基线六类近均匀，LOC 0.214 微弱正确；ABBR 的 1/p_cf 极大 → 分数 271 : 1 坍缩翻错 —— TREC 全规模负收益的机制", options: { fontSize: 20, color: "1F2A36" } },
  ], { x: 8.42, y: 4.35, w: 4.14, h: 2.45, fontFace: FONT, margin: 0, paraSpaceAfter: 6 });
  s.addText("24 例明细：results/案例分析_全量.md（翻转 48802 = 修复 14688 + 破坏 16089 + 双向翻错 18025）",
    { x: 0.55, y: 7.02, w: 12.2, h: 0.36, fontFace: FONT, fontSize: 14, color: C.gray, margin: 0 });
  s.addNotes("左图右案例：修复=先验抑制，破坏=噪声放大；两例都能在逐样本 CSV 复算。");
}

// ============ S7 结论与贡献（深底） ============
{
  const s = pres.addSlide();
  s.background = { color: C.dark };
  s.addText("结论与贡献", { x: 0.55, y: 0.32, w: 12.2, h: 0.62, fontFace: FONT,
    fontSize: 30, bold: true, color: "FFFFFF", margin: 0 });
  const items = [
    ["复现成功", "校准提升平均准确率：≥355M 0-shot SST-2 / AGNews +11~+23pp，方向与论文一致", C.greenOnDark],
    ["复现成功", "Table 3「内容无关输入的选择影响结果、存在多种好选择」完整成立", C.greenOnDark],
    ["机制一致", "先验坍缩与回声补全行为与原文描述相符；案例可逐样本复算", C.greenOnDark],
    ["未复现", "TREC：论文 Table 4 报告 XL 全 shot +13~21pp，本组四模型全负（均匀先验噪声放大）", C.redOnDark],
    ["未复现", "降方差声称：36 个 few-shot 配置中 26 个升方差", C.redOnDark],
  ];
  items.forEach(([tag, body, color], i) => {
    const y = 1.25 + i * 1.06;
    card(s, { x: 0.55, y, w: 7.6, h: 0.92, fill: { color: "FFFFFF", transparency: 90 } });
    s.addText([
      { text: tag + "　", options: { fontSize: 20, bold: true, color } },
      { text: body, options: { fontSize: 20, color: "F2F7FB" } },
    ], { x: 0.8, y, w: 7.1, h: 0.92, fontFace: FONT, valign: "middle", margin: 0 });
  });
  card(s, { x: 8.5, y: 1.25, w: 4.28, h: 5.18, fill: { color: "FFFFFF", transparency: 88 } });
  s.addText([
    { text: "运行证据与可复现性", options: { fontSize: 21, bold: true, color: C.light, breakLine: true } },
    { text: "240 run 全落盘；241 个结果文件独立复算一致", options: { bullet: true, breakLine: true } },
    { text: "24 个案例分析逐样本可复算", options: { bullet: true, breakLine: true } },
    { text: "全量台账 + 两轮对抗评审（工程管理/）", options: { bullet: true, breakLine: true } },
    { text: "AI 辅助：Claude Code 工程执行；方案与判读本组完成", options: { bullet: true } },
  ], { x: 8.74, y: 1.45, w: 3.85, h: 4.8, fontFace: FONT, fontSize: 20, color: "F2F7FB",
      margin: 0, paraSpaceAfter: 10, valign: "top" });
  s.addText("提交包 NLP2026_G17_P33.zip · report.pdf（正文 5 页）· 逐条结果入口见 results/",
    { x: 0.55, y: 6.85, w: 12.2, h: 0.4, fontFace: FONT, fontSize: 16, color: C.iceOnDark,
      align: "center", margin: 0 });
  s.addNotes("收尾：两正一机制 + 两处不一致如实报告；右侧强调证据链与 AI 声明（评分点：错误分析与结论、交付）。");
}

pres.writeFile({ fileName: OUT }).then(() => console.log("WROTE " + OUT));
