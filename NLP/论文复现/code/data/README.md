# 数据说明（data/）

日期：2026-11-03 获取，2026-11-17 复核 SHA256 全部一致。所有文件按作者仓库原样获取，未做任何修改。

## 来源

1. **作者仓库** `tonyzhaozh/few-shot-learning`（master 分支，2026-11-03 经镜像读取）
   - `sst2/stsa.binary.train`（6920 条）、`sst2/stsa.binary.dev`（872 条）
   - `trec/train.txt`（5452 条）、`trec/test.txt`（500 条）
   - `agnews/train.csv`（120000 条）、`agnews/test.csv`（7600 条）、`agnews/classes.txt`
   - 下载渠道：cdn.jsdelivr.net 镜像；agnews/train.csv 经 ghfast.top 镜像
2. **SST-2 测试集** `stsa.binary.test`（1821 条）：作者仓库未附带该文件（其 data_utils 引用但缺失），
   取自 GitHub 公开镜像仓库 `AcademiaSinicaNLPLab/sentiment_dataset`（同为 Socher 等发布的 SST
   二分类标准划分，格式一致：首字符标签 + 空格 + 句子）。已在复现报告（report.pdf §3）中如实声明此差异。

## 上游数据集与许可

- **SST-2**：Socher et al. 2013 情感树库的二分类句子级划分（stanfordSentimentTreebank，仅限研究用途）
- **AGNews**：Zhang et al. 2015（Character-level Convolutional Networks），来自 Yahoo! News 主题分类公开数据
- **TREC**：Voorhees & Tice 2000（TREC-10 QA 问题分类公开数据）

## 固定划分与样本 ID（复现可比性声明）

- **测试集**：每数据集以 seed 0 冻结抽取 300 条（`subsample_test_set=300`），跨 seed 与跨 run 使用
  同一批测试样本；抽中的样本 ID 保存在每次运行结果的 `test_ids` 字段（`results/raw/*.json`）
- **训练样例**（few-shot 示例）：seed 0–4 各抽一次（shots=0/1/4/8），抽中的样本 ID 与文本保存在
  结果的 `train_ids`/`train_sentences` 字段
- 所有随机过程固定种子，同配置可精确复现；重跑命令见上级 `../README.md` 第 4 节

## SHA256 清单（2026-11-17 复核一致）

```
02fedc82855dbdcabe82c65ed1af6c6570788eaac51073cdb35ee8c7784426d1 sst2/stsa.binary.dev
6a80dc9b9a0db2d3b37f2f809304febad31c90ab67a5b4157b7d9f881c53ef5b sst2/stsa.binary.test
71c04bcc41291fa47454dd670df701b14ee9249156babeaac404cfe2c8d74338 sst2/stsa.binary.train
69b2d406aa15b3b514b6bf9b3bf1fa2c3515ce7ae744651173f8e57347bfb2a9 trec/test.txt
202e3e1ad6143ed4f147f199324277e25b2573a78c08c3af1ff840b49c0779de trec/train.txt
1a5783c08f1468ec5200f5b67ef041a2f72a7fe4645aa121769aaf481593663f agnews/classes.txt
1b1b6c5f1dd034c83fec3f585611d2bc65c34fafd86685fc92cee5e6059313ef agnews/test.csv
113bd4d30f9733a4ca0896a69ea90b73e647c5e357e96d394f55fd251d3a8101 agnews/train.csv
```
