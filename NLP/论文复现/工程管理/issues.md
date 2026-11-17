# Issue 台账：Calibrate Before Use 复现工程

> 维护规则：状态只允许 `open / in_progress / in_review / done / blocked / pending`；
> 每次状态变更须同步更新 `run_log.md` 与 `session_log.md`；产出物一律写相对 `论文复现/` 的路径。
> 分两期：**第一期 = 中期进展记录阶段**（2026-11-03 启动，本次会话）；
> **第二期 = 全量复现阶段**（暂 pending，等用户通知后启动）。

---

## 第一期（中期报告阶段）

### I01 P0 工程化基建

- **描述**：建立 `工程管理/` 目录与日志规范——issue 台账（本文件）、运行台账（run_log.md）、操作时间线（session_log.md）、关键决策（decisions.md）、评审目录（review/），作为后续所有执行动作与结论的唯一记录载体。
- **验收标准**：四份台账文件 + review/ 目录说明全部就位；条目格式统一（表格规范、中文字段）；不含作者隐私信息。
- **状态**：done
- **产出物**：`工程管理/issues.md`、`工程管理/run_log.md`、`工程管理/session_log.md`、`工程管理/decisions.md`、`工程管理/review/README.md`
- **备注**：2026-11-03 晚完成初版；后续 issue 状态变更直接改本文件对应字段。

### I02 P1 资源试跑

- **描述**：运行 `code/scripts/run_trial.py`（gpt2 × SST-2 × 4-shot × seed0 × 50 条测试，fp32，bs=16），验证依赖 / 权重 / 数据 / 硬件全链路可用，记录输出、耗时与显存峰值，为全集规模与 bs/fp16 决策（D01/D02/I09）提供实测依据。
- **验收标准**：`results/raw/trial_sst2_gpt2.json` 落盘；日志含基线/校准准确率、p_cf、模型加载与推理耗时、显存峰值；`run_log.md` 对应行回填结束时间与结果。
- **状态**：done（2026-11-03）
- **产出物**：`results/logs/P1_trial.log`、`results/raw/trial_sst2_gpt2.json`
- **备注**：基线 0.4200 / 校准 0.5000 / p_cf [0.565, 0.435] / 显存峰值 2.18 GB / 全程 3s（加载 2s + 推理 1s）；`scripts/check_results.py` 字段校验通过。显存余量充足（8GB 卡仅用 2.18GB），支持 D02 的 bs=16 与 D01 的 fp32 优先。

### I03 P2 冒烟全链路

- **描述**：运行 `calib/experiment.py`（gpt2 × sst2 × shots 0,1,4,8 × seed0 × sub300 × bs16，fp32），验证 `run_one` 完整落盘链路：raw JSON（配置+训练样例+逐样本）+ samples CSV + summary.csv 追加，以及"已存在自动跳过"的断点安全机制。
- **验收标准**：4 个配置的 raw JSON 与 samples CSV 全部落盘、summary.csv 追加 4 行；重跑同一命令时 4 个 run 均提示"跳过（已存在）"；结果数字进入 I04/I05。
- **状态**：done（2026-11-03）
- **产出物**：`results/logs/P2_smoke_gpt2_sst2.log`、`results/raw/sst2_gpt2_{0,1,4,8}shot_sub300_seed0.json` 与 `results/samples/` 同名 CSV、`results/summary.csv` 4 行
- **备注**：首次启动失败（ModuleNotFoundError，详见 run_log 异常列）后于源头修复：`experiment.py` 头部加 `sys.path.insert(code/)`，README 命令原样可跑。重试 4/4 run 落盘；重跑同命令 4/4 提示"跳过（已存在）"，断点安全机制验证通过（D04 生效）。另扩 P2b（agnews/trec）8/8 落盘，三数据加载器全路径验证；`scripts/check_results.py` 独立复算 13/13 一致。

### I04 中期进展记录编写

- **描述**：按课程规范"中期进展记录"要求编写一页文档，六字段：①原文目标位置 ②本组设置差异 ③已有并列结果 ④本组运行生成的逐条输出链接 ⑤两例失败或边界案例 ⑥下一项单因素实验；全部使用真实运行数字，不编造进度。
- **验收标准**：六字段齐全、篇幅一页以内；每个数字均可溯源到 `results/` 下具体文件；失败/边界案例与 I05 一致；如 P2 未跑通则如实给出错误信息与已完成的环境/资源检查。
- **状态**：done（2026-11-04，R01 整改 5 处引用/数值后经 R01b 增量复核通过）
- **产出物**：`中期进展记录.md`（位于 `论文复现/` 根目录）
- **备注**：六字段齐全；③为 12 行三数据集结果表 + Table 1（GPT-3 175B K=4）与 Table 4（GPT-2 XL）双论文参照表 + "校准收益规模依赖"观察；⑤两例主边界（TREC 8-shot 校准坍缩、SST-2 0-shot 弱先验噪声放大）+ 正面机制确认（AGNews 1-shot +28.7pp）；每个数字经 R01/R01b 两轮复核溯源一致。

### I05 失败/边界案例提取

- **描述**：从冒烟结果逐样本 CSV（`results/samples/*.csv`）提取 ≥2 例真实案例，优先筛选"校准翻转预测"（pred_original ≠ pred_calibrated，可用 raw JSON 的 num_flip 定位配置）与"回声补全触发"的样本；逐例记录 sample_id、gold、两套预测、各类概率与触发机制解释。
- **验收标准**：≥2 例且均来自真实落盘 CSV，每例可复算（sample_id 能在 `code/data/` 原始数据文件中定位原文）；机制解释与概率数值一致。
- **状态**：done（2026-11-04，并入 I04 第⑤字段，经 R01/R01b 复核通过）
- **产出物**：`中期进展记录.md` 第⑤字段
- **备注**：提取了 2 主例 + 2 附例，全部来自真实落盘数据：① TREC 8-shot 校准坍缩（翻转 300/300，num_flip 见 summary.csv）；② SST-2 0-shot 弱先验噪声放大（翻转 88/300）；附 AGNews 1-shot 先验坍缩正收益（翻转 262/300，p_cf Technology 0.810）与回声补全触发统计（SST-2 0-shot 319/600、AGNews 0-shot 1343 个标签概率缺失，见运行日志）。样本级细节可从 `results/samples/*.csv` 按 pred_original≠pred_calibrated 筛选复核。

### I06 Review R01 评审

- **描述**：由 review 代理对第一期成果做对抗评审，三方面：① P1/P2 结果合理性（准确率量级、p_cf 分布、耗时显存是否符合预期）；② 本组代码与作者代码（`作者代码/few-shot-learning/`）逐行对照复核；③ 中期进展记录真实性（数字与 `results/` 落盘文件逐一核对）。
- **验收标准**：R01 评审记录落在 `工程管理/review/`；三方面均有明确结论与证据；给出"通过 / 需整改"结论，整改项回填为 issue。
- **状态**：done（2026-11-04，R01 完成：维度1 PASS / 维度2 PASS-with-notes / 维度3 FAIL（仅 5 处论文引用错误）/ 维度4 PASS-with-notes，总体"有条件通过"）
- **产出物**：`工程管理/review/R01_中期阶段评审.md`
- **备注**：GPU 端到端复算 300/300 逐条一致、p_cf 逐位相同，未发现编造；整改清单 9 项已由主循环落实（P-1~P-5 中期记录更正、P-9 跳过前配置校验、P-10 作者两文件补落盘、P-11 README §6 补声明、消融对齐论文设置），文字整改后待 R01b 增量复核。

---

## 第二期（全量复现阶段，暂 pending，等用户通知）

### I07 全网格运行

- **描述**：4 模型（gpt2 / medium / large / xl）× 3 数据集（sst2 / agnews / trec）× 4 shots（0/1/4/8）× 5 seeds = 240 run；按模型分批后台执行（README 预计 gpt2 约 10 分钟、xl 单数据集 3-4 小时，fp32）；断点安全：已存在 run 自动跳过，冒烟的 4 个 seed0 run 可复用（D04）。
- **验收标准**：240 run 全部落盘（raw JSON + samples CSV），summary.csv 240 行；`--aggregate_only` 能输出全部聚合行；失败 run 有异常记录与重试结果。
- **状态**：done（2026-11-16 01:35–03:15，240/240 run 全落盘，12 次数据集调用全部一次通过零重试，总耗时 1h40m；`check_results.py` 241 文件全量独立复算通过）
- **产出物**：`results/raw/`（240 JSON）、`results/samples/`（240 CSV）、`results/summary.csv`（240 行）、`results/logs/I07_*.log`（12 个数据集日志 + master）
- **备注**：启动方式须避开 I03 已发现的 ModuleNotFoundError（`python -m calib.experiment`）；bs 按 D02 显式传参。批次驱动 `scripts/run_grid_batch.sh`（单数据集失败同 bs 重试 3 次、mkdir logs、PYTHONUNBUFFERED 实时日志，经 2026-11-16 对抗评审修复 2 项）。实测耗时：gpt2 6.6min / medium 13.5min / large 27.2min / xl 52.5min；AGNews 有 3 处 allocator 自恢复 OOM 告警（gpt2×2、medium×1，未中断批次，同 P2b 性质）。

### I08 修复 --cf_ablation 失效 bug

- **描述**：`code/calib/experiment.py` 中消融 run 调用 `run_one(..., content_free_inputs=("N/A",))` 等，但 `expr_name` 格式串不含 content_free_inputs 字段，与主 run 同名 → 命中"已存在跳过"去重逻辑，消融结果与主 run 完全相同，Table 3 消融实际未执行。修复方案：不动主链路，另写离线消融脚本——从已有 samples CSV 读逐样本概率，只需为各内容无关输入补少量 p_cf 前向（3 条输入/配置），离线重算消融准确率。
- **验收标准**：消融脚本对任一已有 run 能产出与主 run 区分开的消融结果（独立文件名落盘）；N/A / [MASK] / 空串 / 三者平均 四种选择的准确率各不相同（若相同给出解释）；抽样人工复算 1 例一致。
- **状态**：done（2026-11-16，脚本干跑验证 12 配置 + I10 全量 40 run 两道防线全过；经对抗评审修复 3 处：GPT2Runner.bs 未初始化、四模型同进程显存累积、prompt 模板漂移校验缺失）
- **产出物**：`code/scripts/cf_ablation_offline.py` + `results/cf_ablation/`（50 个 run 级 JSON + cf_ablation_summary.csv）
- **备注**：2026-11-03 会话发现；离线方案验收全达成：四种选择准确率可区分（坍缩组除外，已有解释——argmax 在坍缩类上对 p_cf 不敏感）且 seed0 独立内联复算逐位一致。首个消融数字即证论文 Table 3 现象：TREC 8-shot 三输入平均 0.0333 vs [MASK] 0.2400。

### I09 bs/fp16 决策落档

- **描述**：把 batch size 与精度的最终决策写入 `工程管理/decisions.md`。已知不一致：`code/README.md` 说"按模型 16/12/8/4"，而 `experiment.py` 的 `--bs` 默认 None → `set_batch_size(bs or 4)` 实际默认 4，不显式传参会慢约 4 倍。依据 I02 显存实测（gpt2 bs16 fp32 仅 2.18GB / 8GB 卡）逐模型核定 bs，fp16 与否按 D01 视 gpt2-xl 试跑而定。
- **验收标准**：decisions.md 中 D02 状态更新为"生效"并附各模型实测显存数字；README 第 4 节与实际命令一致（如需改 README 另记变更）。
- **状态**：done（2026-11-15，探针核定 12 组合全落档，xl 维持 fp32 见 D02）
- **产出物**：`工程管理/decisions.md`（D02/D05 生效版全表）、`code/scripts/bs_probe.py`、`results/probes/*.json`（14 个探针）、`results/logs/I09_bs_probe.log`
- **备注**：新发现：gpt2-xl fp32 全候选 bs 超物理显存但 WDDM 溢出兜底无一 OOM，bs2 反而快于 bs4（agnews 37.3s vs 72.1s / 51 条）——按 D01 框架维持 fp32 + 溢出档；README §4 的 bs 建议表待 I07 后随状态行一并更新。

### I10 Table 3 消融执行

- **描述**：内容无关输入选择消融（N/A vs [MASK] vs 空串 vs 三者平均，对应论文 Table 3），经 I08 的离线方案在全部 240 run 的落盘数据上执行；**优先按论文 Table 3 的设置（1-shot SST-2、0-shot AGNews）执行**，与原文可比性更强（R01 建议）。
- **验收标准**：每个（模型 × 数据集 × shot）配置有四种内容无关输入选择的准确率对比；汇总表可并入最终报告。
- **状态**：done（2026-11-16 03:16–03:17，论文 Table 3 设置执行完毕：sst2:1 + agnews:0 × 4 模型 × 5 seeds = 40 run，exit 0，两道防线全过）
- **产出物**：`results/cf_ablation/`（含 cf_ablation_summary.csv 50 行）、`results/logs/I10_cf_ablation.log`、聚合表见脚本输出归档
- **备注**：论文结论"内容无关输入的选择影响结果，且存在多种好选择"复现成立：xl AGNews 0-shot 空串 0.5733 vs 三输入平均 0.5200（差 5.3pp）；四值互异性按 5-seed 均值口径 8 组中 6 组互异、2 组全同（medium-agnews 与 large-sst2，均为坍缩机制：argmax 对 p_cf 不敏感，如实解释；2026-11-17 对抗复核更正）。**口径（R01b B4）**：缺失计数为类粒度，与历史词粒度不可混比。

### I11 汇总与图

- **描述**：`--aggregate_only` 输出均值±std 聚合表（另存 `results/aggregate.txt`）；绘制论文 Figure 1 风格图（准确率均值±std 随 shot 变化，基线 vs 校准）；案例分析扩到 ≥10 例（校准翻转预测优先）。
- **验收标准**：聚合表覆盖全部 240 run；图与论文 Figure 1（GPT-2 部分）可比；案例均来自真实逐样本 CSV 且可复算。
- **状态**：done（2026-11-16，aggregate 48 组全覆盖 + fig3/fig4 全量版编译 0 错误 + 案例分析 24 例人工复算 2 例逐位一致）
- **产出物**：`results/aggregate.txt`、`材料/figures/fig3_fullgrid_acc.{tex,pdf,png}`、`材料/figures/fig4_table3_ablation.{tex,pdf,png}`、`工程管理/案例分析_全量.md`（翻转 48802 = 修复 14688 + 破坏 16089 + 双向翻错 18025）；生成脚本 `scripts/make_fullfigs.py`、`scripts/extract_cases.py`
- **备注**：画图规范首选 latex-figure 流程产出矢量 PDF（fig3 4×3 面板折线均值±std、fig4 Table 3 分组柱状）；案例分析三类账并列（双向翻错单独成类，评审修复项）；新增脚本均经 14-agent 对抗评审 + 运行时复现验证。

### I12 最终提交物

- **描述**：report（4-6 页）+ slides（7 页）+ README 终稿 + contributions.md + 打包自检（NLP2026_Gxx_Pxx.zip），对齐提交规范最终包清单。
- **验收标准**：包内清单齐全（report/slides/README/code+configs/results/data/contributions）；README 含环境版本、数据取得、命令、预计耗时、逐条结果入口；自检通过。
- **状态**：done（2026-11-17，组号 G17 / 论文号 P33，分工栏按要求留白待组内填写）
- **产出物**：`report.pdf`（正文 6 页：定位/差异/结果/消融/案例/结论，第 6 页同页含参考文献与附录 A，符合 4–6 页规范）+ `report.tex` 源 + `slides.pptx`/`slides.pdf`（7 页 16:9，标题 30pt/正文 20pt/表 18pt 达标）+ `README.md`（项目总说明）+ `contributions.md` + `NLP2026_G17_P33.zip`（606 条目 15.6MB，自检：无重复、CRC 全过、无权重/缓存）+ `材料/最终材料.zip`（60 条目 1.9MB）+ 打包脚本 `scripts/package_submission.py`
- **备注**：全工程以独立项目呈现并分 5 次提交推送双平台（Gitee li_fjyr/project + GitHub song-xunxue/project，d68257a..9998645）；zip 经 .gitattributes 取反走普通二进制（Gitee 免费版无 LFS）；数据说明升格 `code/data/README.md`（SHA256 复核 8/8 一致）；`data/数据来源.md`、`复现计划.md` 已合并/删除。报告数字另经多代理对抗复核。
