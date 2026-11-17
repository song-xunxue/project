"""生成全量复现结果图：从 results/raw 与 results/cf_ablation 读数，产出 pgfplots 的 .tex 源。

日期: 2026-11-16

2026-11-16
变更说明：
  1. 初版：fig3 全网格准确率曲线（4 模型 x 3 数据集 = 12 面板，基线 vs 校准均值±std 误差棒
     随 shot 变化，附随机水平虚线——论文 Figure 1 GPT-2 部分风格）；fig4 Table 3 消融
     分组柱状图（sst2 1-shot / agnews 0-shot 两面板 x 4 模型，四种内容无关输入选择）。
     用法：PYTHONUTF8=1 python scripts/make_fullfigs.py
     产物：论文复现/材料/figures/fig3_fullgrid_acc.tex、fig4_table3_ablation.tex（需再 xelatex 编译）
  2. 与已交付的 make_midterm_figs.py 相互独立（中期图保持可复现，不改动）。
  3. pgfplots 写法沿用中期脚本已验证的 MiKTeX 兼容模式（/tikz/ 路径的 bar width、
     参考线 sharp plot、无下划线字符）。
"""
import json
import statistics
from collections import defaultdict
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent.parent          # 论文复现/code
RESULTS_DIR = CODE_DIR.parent / "results"                  # 论文复现/results
OUT_DIR = CODE_DIR.parent / "材料" / "figures"             # 论文复现/材料/figures

MODELS = [("gpt2", "GPT-2"), ("gpt2-medium", "GPT-2 Medium"),
          ("gpt2-large", "GPT-2 Large"), ("gpt2-xl", "GPT-2 XL")]
DATASETS = [("sst2", "SST-2（二类）"), ("agnews", "AGNews（四类）"), ("trec", "TREC（六类）")]
SHOTS = [0, 1, 4, 8]
RANDOM_LEVEL = {"sst2": 50.0, "agnews": 25.0, "trec": 16.67}
# Table 3 消融的论文设置（R01 建议）：1-shot SST-2、0-shot AGNews
ABL_SETTINGS = [("sst2", 1, "SST-2 1-shot"), ("agnews", 0, "AGNews 0-shot")]
ABL_VARIANTS = [("acc_diag_full", "三输入平均"), ("acc_diag_N/A", "N/A"),
                ("acc_diag_[MASK]", "[MASK]"), ("acc_diag_empty", "空串")]


def collect_grid():
    """全部 raw JSON 按（模型, 数据集, shot）聚合，返回 {(m,d,s): ([基线acc...], [校准acc...])}。"""
    groups = defaultdict(lambda: ([], []))
    for path in sorted((RESULTS_DIR / "raw").glob("*.json")):
        r = json.loads(path.read_text(encoding="utf-8"))
        if "config" not in r or r.get("trial"):
            continue  # trial/probe 类文件不进图
        c = r["config"]
        orig, cal = groups[(c["model"], c["dataset"], c["num_shots"])]
        orig.append(r["accuracies"]["original"] * 100)
        cal.append(r["accuracies"]["diagonal_W"] * 100)
    return groups


def collect_ablation():
    """cf_ablation JSON 按（模型, 数据集, shot）聚合，返回 {(m,d,s): {variant键: 均值}}。"""
    groups = defaultdict(lambda: defaultdict(list))
    for path in sorted((RESULTS_DIR / "cf_ablation").glob("*.json")):
        if path.name == "cf_ablation_summary.csv":
            continue
        r = json.loads(path.read_text(encoding="utf-8"))
        for key, _ in ABL_VARIANTS:
            groups[(r["model"], r["dataset"], r["shots"])][key].append(r[key] * 100)
    return {k: {key: statistics.mean(v) for key, v in d.items()} for k, d in groups.items()}


def mean_std(vals):
    m = statistics.mean(vals)
    s = statistics.stdev(vals) if len(vals) > 1 else 0.0
    return m, s


def fig3_fullgrid(groups):
    """fig3：4x3 面板折线图，基线 vs 校准 均值±std 随 shot 变化。"""
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
  group style={group size=3 by 4, horizontal sep=1.35cm, vertical sep=1.5cm},
  width=5.2cm, height=4.6cm,
  ymin=0, ymax=100,
  xtick=data, tick label style={font=\scriptsize},
  xlabel={shot 数}, xlabel style={font=\small},
  symbolic x coords={0,1,4,8},
  title style={font=\small\bfseries},
  enlarge x limits=0.12,
  legend style={font=\scriptsize},
]
"""
    body = ""
    for row, (model, model_label) in enumerate(MODELS):
        for col, (ds, ds_label) in enumerate(DATASETS):
            opts = f"[title={{{ds_label}}}"
            if col == 0:
                opts += f", ylabel={{{model_label}}}, ylabel style={{font=\\small}}"
            if row == 0 and col == 0:
                opts += (", legend pos=south east, legend cell align=left")
            opts += "]"
            body += f"\\nextgroupplot{opts}\n"
            lvl = RANDOM_LEVEL[ds]
            for key, color, legend, first in (
                    ("orig", "primary!90!accent", "基线", row == 0 and col == 0),
                    ("cal", "accent", "校准", False)):
                series = ""
                for sh in SHOTS:
                    accs = groups.get((model, ds, sh))
                    if not accs:
                        continue
                    arr = accs[0] if key == "orig" else accs[1]
                    m, s = mean_std(arr)
                    series += f" ({sh},{m:.2f}) +- (0,{s:.2f})"
                if not series:
                    continue
                line = (f"\\addplot[color={color}, mark=*, mark size=1.6pt, thick, "
                        f"error bars/.cd, y dir=both, y explicit] coordinates {{{series}}};\n")
                body += line
                if first:
                    body += "\\addlegendentry{基线}\n"
                elif key == "cal" and row == 0 and col == 0:
                    body += "\\addlegendentry{校准}\n"
            body += (f"\\addplot[dashed, thick, red!70!black, sharp plot, update limits=false] "
                     f"coordinates {{(0,{lvl}) (8,{lvl})}};\n")
            if row == 0 and col == 0:
                body += "\\addlegendentry{随机水平}\n"
    tail = "\\end{groupplot}\n\\end{tikzpicture}\n\\end{document}\n"
    return head + body + tail


def fig4_table3(abl):
    """fig4：Table 3 消融分组柱状图，两面板（论文设置）x 4 模型 x 四种内容无关输入。"""
    MODEL_COORDS = {"gpt2": "G2", "gpt2-medium": "G2M", "gpt2-large": "G2L", "gpt2-xl": "G2XL"}
    head = r"""\documentclass[border=2mm]{standalone}
\usepackage{ctex}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\usepgfplotslibrary{groupplots}
\definecolor{c1}{HTML}{79C4FE}
\definecolor{c2}{HTML}{3D9AE2}
\definecolor{c3}{HTML}{0B6FB8}
\definecolor{c4}{HTML}{0A4C85}
\begin{document}
\begin{tikzpicture}
\begin{groupplot}[
  group style={group size=2 by 1, horizontal sep=1.6cm},
  width=8.6cm, height=6.2cm,
  ybar, /tikz/bar width=7pt,
  ymin=0, ymax=85,
  symbolic x coords={G2,G2M,G2L,G2XL}, xtick=data,
  xticklabels={GPT-2, Medium, Large, XL},
  xlabel={模型}, xlabel style={font=\small},
  ylabel={校准准确率 (\%)}, ylabel style={font=\small},
  tick label style={font=\scriptsize},
  title style={font=\small\bfseries},
  enlarge x limits=0.15,
  legend style={font=\scriptsize, at={(0.5,-0.22)}, anchor=north, legend columns=4},
]
"""
    body = ""
    for panel, (ds, shots, title) in enumerate(ABL_SETTINGS):
        opts = f"[title={{{title}}}"
        if panel == 0:
            opts += ", legend pos=north west"
        opts += "]"
        body += f"\\nextgroupplot{opts}\n"
        for i, (key, label) in enumerate(ABL_VARIANTS):
            series = ""
            for model, _ in MODELS:
                v = abl.get((model, ds, shots), {}).get(key)
                if v is not None:
                    series += f"({MODEL_COORDS[model]},{v:.2f}) "
            body += f"\\addplot[fill=c{i + 1}, draw=c4!80] coordinates {{{series}}};\n"
            if panel == 0:
                body += f"\\addlegendentry{{{label}}}\n"
    tail = "\\end{groupplot}\n\\end{tikzpicture}\n\\end{document}\n"
    return head + body + tail


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    groups = collect_grid()
    n_runs = sum(len(a) for a, _ in groups.values())
    print(f"读入 {n_runs} 个 run，覆盖 {len(groups)} 个（模型,数据集,shot）组")
    missing = [(m, d, s) for m, _ in MODELS for d, _ in DATASETS for s in SHOTS
               if (m, d, s) not in groups]
    if missing:
        print(f"警告：{len(missing)} 组缺失（网格未完成时属预期）：{missing[:6]}...")
    (OUT_DIR / "fig3_fullgrid_acc.tex").write_text(fig3_fullgrid(groups), encoding="utf-8")

    abl = collect_ablation()
    if abl:
        (OUT_DIR / "fig4_table3_ablation.tex").write_text(fig4_table3(abl), encoding="utf-8")
        print(f"消融数据 {len(abl)} 组，fig4 已生成")
    else:
        print("消融数据为空（I10 未跑），fig4 跳过")
    for f in ("fig3_fullgrid_acc.tex", "fig4_table3_ablation.tex"):
        p = OUT_DIR / f
        if p.exists():
            print(f"  {f} ({p.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
