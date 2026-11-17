"""生成中期报告结果图：从 results/raw/*.json 读数，产出 pgfplots/TikZ 的 .tex 源文件。

日期: 2026-11-04

2026-11-04
变更说明：
  1. 初版：图1 三数据集基线vs校准准确率分组柱状图（带随机水平虚线，pgfplots groupplots）；
     图2 校准先验 p_cf 热力矩阵（行=shot、列=类，色深∝数值，TikZ 手排矩阵）。
     用法：PYTHONUTF8=1 python scripts/make_midterm_figs.py
     产物：论文复现/材料/figures/fig1_acc_compare.tex、fig2_pcf_heatmap.tex（需再 xelatex 编译）
"""
import json
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent.parent          # 论文复现/code
RESULTS_DIR = CODE_DIR.parent / "results"                  # 论文复现/results
OUT_DIR = CODE_DIR.parent / "材料" / "figures"             # 论文复现/材料/figures

DATASETS = [("sst2", "SST-2（二类）"), ("agnews", "AGNews（四类）"), ("trec", "TREC（六类）")]
SHOTS = [0, 1, 4, 8]
RANDOM_LEVEL = {"sst2": 50.0, "agnews": 25.0, "trec": 16.67}
CLASS_NAMES = {
    "sst2": ["Negative", "Positive"],
    "agnews": ["World", "Sports", "Business", "Tech.\\,Sci"],
    "trec": ["NUM", "LOC", "HUM", "DESC", "ENTY", "ABBR"],
}


def load_results():
    """读取 12 个 run 的准确率与 p_cf，返回 {dataset: {shot: (acc_orig, acc_cal, p_cf)}}。"""
    out = {}
    for ds, _ in DATASETS:
        out[ds] = {}
        for sh in SHOTS:
            path = RESULTS_DIR / "raw" / f"{ds}_gpt2_{sh}shot_sub300_seed0.json"
            r = json.loads(path.read_text(encoding="utf-8"))
            a = r["accuracies"]
            out[ds][sh] = (a["original"] * 100, a["diagonal_W"] * 100, r["p_cf"])
    return out


def fig1_acc(res):
    """图1：三面板分组柱状图，基线 vs 校准，附随机水平虚线。"""
    head = r"""\documentclass[border=2mm]{standalone}
\usepackage{ctex}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\usepgfplotslibrary{groupplots}
\definecolor{primary}{HTML}{79C4FE}
\definecolor{accent}{HTML}{0B6FB8}
\begin{document}
\begin{tikzpicture}
\begin{groupplot}[
  group style={group size=3 by 1, horizontal sep=1.45cm},
  width=5.5cm, height=5.6cm,
  ybar, /tikz/bar width=9pt,
  ymin=0, ymax=85,
  ylabel={准确率 (\%)}, ylabel style={font=\small},
  xlabel={shot 数}, xlabel style={font=\small},
  symbolic x coords={0,1,4,8}, xtick=data,
  tick label style={font=\small},
  title style={font=\small\bfseries},
  enlarge x limits=0.18,
]
"""
    body = ""
    for i, (ds, title) in enumerate(DATASETS):
        orig = " ".join(f"({sh},{res[ds][sh][0]:.2f})" for sh in SHOTS)
        cal = " ".join(f"({sh},{res[ds][sh][1]:.2f})" for sh in SHOTS)
        lvl = RANDOM_LEVEL[ds]
        opts = "[title={" + title + "}]"
        if i == 0:
            opts = "[title={" + title + "}, legend pos=north east, legend style={font=\\scriptsize}]"
        body += f"\\nextgroupplot{opts}\n"
        body += f"\\addplot[fill=primary, draw=accent!80] coordinates {{{orig}}};\n"
        if i == 0:
            body += "\\addlegendentry{基线}\n"
        body += f"\\addplot[fill=accent, draw=accent!80] coordinates {{{cal}}};\n"
        if i == 0:
            body += "\\addlegendentry{校准}\n"
        body += (f"\\addplot[dashed, thick, red!70!black, sharp plot, update limits=false] "
                 f"coordinates {{(0,{lvl}) (8,{lvl})}};\n")
        if i == 0:
            body += "\\addlegendentry{随机水平}\n"
    tail = "\\end{groupplot}\n\\end{tikzpicture}\n\\end{document}\n"
    return head + body + tail


def fig2_pcf(res):
    """图2：p_cf 热力矩阵（行=shot、列=类、色深∝数值）。"""
    CELL_W, CELL_H = 1.05, 0.62
    GAP = 0.55  # 三个数据集矩阵之间的间隔（厘米）
    rows = []
    x = 0.0
    head = r"""\documentclass[border=2mm]{standalone}
\usepackage{ctex}
\usepackage{tikz}
\definecolor{accent}{HTML}{0B6FB8}
\begin{document}
\begin{tikzpicture}[font=\scriptsize]
"""
    body = ""
    x_cur = 0.0
    for ds, title in DATASETS:
        names = CLASS_NAMES[ds]
        n_cls = len(names)
        # 面板标题
        cx = x_cur + n_cls * CELL_W / 2
        body += f"\\node[font=\\small\\bfseries] at ({cx:.3f}, {CELL_H * len(SHOTS) + 1.15}) {{{title}}};\n"
        # 列头（类名，旋转 30 度防重叠）
        for j, name in enumerate(names):
            colx = x_cur + j * CELL_W + CELL_W / 2
            ytop = CELL_H * len(SHOTS) + 0.72
            body += (f"\\node[rotate=30, anchor=east, font=\\scriptsize] "
                     f"at ({colx:.3f}, {ytop:.3f}) {{{name}}};\n")
        # 行标签 + 单元格
        for i, sh in enumerate(SHOTS):
            y_mid = CELL_H * (len(SHOTS) - 1 - i) + CELL_H / 2
            body += (f"\\node[anchor=east, font=\\scriptsize] "
                     f"at ({x_cur - 0.12:.3f}, {y_mid:.3f}) {{{sh}}};\n")
            p_cf = res[ds][sh][2]
            for j in range(n_cls):
                v = p_cf[j]
                shade = int(round(v * 100))
                colx = x_cur + j * CELL_W + CELL_W / 2
                cell_y = CELL_H * (len(SHOTS) - 1 - i)
                textcol = "white" if shade >= 55 else "accent!80!black"
                body += (f"\\fill[accent!{shade}!white, draw=gray!45] "
                         f"({x_cur + j * CELL_W:.3f}, {cell_y:.3f}) "
                         f"rectangle ({x_cur + (j + 1) * CELL_W:.3f}, {cell_y + CELL_H:.3f});\n")
                body += (f"\\node[text={textcol}, font=\\scriptsize] "
                         f"at ({colx:.3f}, {y_mid:.3f}) {{{v:.2f}}};\n")
        x_cur += n_cls * CELL_W + GAP
    # 底部色标（0 → 1 渐变图例）
    leg_y = -1.05
    body += f"\\node[anchor=east, font=\\scriptsize] at (-0.12, {leg_y + 0.18}) {{p\\_cf：}};\n"
    for k in range(11):
        shade = k * 10
        body += (f"\\fill[accent!{shade}!white, draw=gray!45] "
                 f"({k * 0.42:.3f}, {leg_y:.3f}) rectangle ({(k + 1) * 0.42:.3f}, {leg_y + 0.3:.3f});\n")
    for k, lab in enumerate(["0", "0.5", "1.0"]):
        # 刻度对准第 0/5/10 个色块的中心（色块宽 0.42，中心偏移 +0.21）
        body += (f"\\node[font=\\scriptsize, anchor=north] "
                 f"at ({k * 5 * 0.42 + 0.21:.3f}, {leg_y - 0.02}) {{{lab}}};\n")
    body += (f"\\node[font=\\scriptsize, anchor=west] at ({6.3:.3f}, {leg_y + 0.15}) "
             f"{{行=shot 数，列=类别，色深 $\\propto$ 先验概率}};\n")
    tail = "\\end{tikzpicture}\n\\end{document}\n"
    return head + body + tail


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    res = load_results()
    (OUT_DIR / "fig1_acc_compare.tex").write_text(fig1_acc(res), encoding="utf-8")
    (OUT_DIR / "fig2_pcf_heatmap.tex").write_text(fig2_pcf(res), encoding="utf-8")
    print(f"已生成 .tex 到 {OUT_DIR}")
    for f in ("fig1_acc_compare.tex", "fig2_pcf_heatmap.tex"):
        print(f"  {f} ({(OUT_DIR / f).stat().st_size} bytes)")


if __name__ == "__main__":
    main()
