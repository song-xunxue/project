"""打包提交物：生成 最终材料.zip（写作参考材料包）与 NLP2026_G17_P33.zip（课程最终提交包）。

日期: 2026-11-17

2026-11-17
变更说明：
  1. 初版：最终材料包 = 图件 + 全部日志 + 全部 md 文档 + 报告/幻灯片 + 关键汇总数据；
     提交包按课程规范清单（report / slides pptx+pdf / README / code+configs / results /
     contributions），排除模型权重、__pycache__、*.pyc。
  2. 自检：条目去重检测、必需文件存在性检测、条目计数与总体积输出。
  3. 用法：PYTHONUTF8=1 python scripts/package_submission.py
"""
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent   # 论文复现/
MATERIALS_ZIP = ROOT / "材料" / "最终材料.zip"
SUBMISSION_ZIP = ROOT / "NLP2026_G17_P33.zip"


def add_files(zf, paths, base=ROOT):
    """把相对路径列表写入 zip（arcname 用相对 论文复现/ 的 POSIX 路径）。"""
    for rel in paths:
        p = base / rel
        if not p.is_file():
            raise FileNotFoundError(f"打包清单中的文件不存在: {rel}")
        arcname = Path(rel).as_posix()
        zf.write(p, arcname)


def add_tree(zf, folder, exclude_dirs=("__pycache__",), exclude_ext=(".pyc",)):
    """递归加入目录（相对 ROOT），按目录名与扩展名排除。"""
    for p in sorted((ROOT / folder).rglob("*")):
        if p.is_file():
            rel = p.relative_to(ROOT)
            if any(part in exclude_dirs for part in rel.parts):
                continue
            if p.suffix in exclude_ext:
                continue
            zf.write(p, rel.as_posix())


def build_materials():
    """最终材料包：图 + 日志 + md 文档 + 报告/幻灯片 + 关键汇总数据。"""
    files = [
        "README.md", "contributions.md", "中期进展记录.md",
        "report.pdf", "report.tex", "slides.pptx", "slides.pdf",
        "code/README.md", "code/data/README.md",
        "results/summary.csv", "results/aggregate.txt", "results/案例分析_全量.md",
        "results/cf_ablation/cf_ablation_summary.csv", "results/probes/probe_summary.json",
    ]
    with zipfile.ZipFile(MATERIALS_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        add_files(zf, files)
        add_tree(zf, "results/logs")
        add_tree(zf, "工程管理")
        add_tree(zf, "材料/figures")
    return MATERIALS_ZIP


def build_submission():
    """课程提交包：规范清单 + 全部 code（除权重/缓存）+ 全部 results。"""
    files = ["report.pdf", "slides.pptx", "slides.pdf", "README.md", "contributions.md"]
    with zipfile.ZipFile(SUBMISSION_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        add_files(zf, files)
        add_tree(zf, "code", exclude_dirs=("__pycache__", "models"), exclude_ext=(".pyc",))
        add_tree(zf, "results")
    return SUBMISSION_ZIP


def self_check(zip_path, required):
    """自检：重复条目检测 + 必需文件存在 + 计数与体积。"""
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        dup = {n for n in names if names.count(n) > 1}
        assert not dup, f"{zip_path.name} 存在重复条目: {dup}"
        missing = [r for r in required if r not in names]
        assert not missing, f"{zip_path.name} 缺必需文件: {missing}"
        bad = zf.testzip()
        assert bad is None, f"{zip_path.name} CRC 校验失败: {bad}"
        size = sum(i.file_size for i in zf.infolist())
        print(f"[OK] {zip_path.name}: {len(names)} 条目, 原始 {size/1e6:.1f} MB, "
              f"压缩后 {zip_path.stat().st_size/1e6:.1f} MB, CRC 全过, 无重复")
        return names


def main():
    MATERIALS_ZIP.parent.mkdir(parents=True, exist_ok=True)
    build_materials()
    m_required = ["README.md", "report.pdf", "slides.pdf", "results/summary.csv",
                  "results/aggregate.txt", "results/案例分析_全量.md",
                  "results/logs/I07_master.log", "材料/figures/fig3_fullgrid_acc.pdf",
                  "工程管理/issues.md", "工程管理/decisions.md"]
    m_names = self_check(MATERIALS_ZIP, m_required)

    build_submission()
    s_required = ["report.pdf", "slides.pptx", "slides.pdf", "README.md",
                  "contributions.md", "code/README.md", "code/data/README.md",
                  "code/calib/experiment.py", "code/scripts/package_submission.py",
                  "results/summary.csv", "results/案例分析_全量.md",
                  "results/logs/I07_master.log"]
    s_names = self_check(SUBMISSION_ZIP, s_required)
    forbidden = [n for n in s_names if n.startswith("code/models/")
                 or "__pycache__" in n or n.endswith(".pyc")]
    assert not forbidden, f"提交包含违禁条目（权重/缓存）: {forbidden[:5]}"
    print("[OK] 提交包含权重/缓存检查通过")


if __name__ == "__main__":
    main()
