"""数据加载与 prompt 格式定义（对齐作者仓库 data_utils.py / load_dataset）。

日期: 2026-11-03

2026-11-03
变更说明：
  1. 初版：SST-2 / AGNews / TREC 三个文本分类数据集；
     数据文件为作者仓库原始文件（code/data/ 下），prompt 前后缀与标签词与作者逐字一致。
"""
from pathlib import Path

# 工程根 = 本文件的上级目录（code/）
CODE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = CODE_DIR / "data"
MODELS_DIR = CODE_DIR / "models"


def load_sst2():
    """SST-2 二分类情感。文件格式：每行首字符为标签(0/1)，其余为句子。"""
    def parse(lines):
        labels = [int(line[0]) for line in lines]
        sentences = [line[2:].strip() for line in lines]
        return sentences, labels

    with open(DATA_DIR / "sst2" / "stsa.binary.train", "r", encoding="utf-8") as f:
        train_sentences, train_labels = parse(f.readlines())
    with open(DATA_DIR / "sst2" / "stsa.binary.test", "r", encoding="utf-8") as f:
        test_sentences, test_labels = parse(f.readlines())
    return train_sentences, train_labels, test_sentences, test_labels


def load_agnews():
    """AGNews 四分类主题。csv 三列：Class Index(1-4), Title, Description。
    与作者一致：文本 = Title + '. ' + Description（含其基础清洗），标签转为 0-3。"""
    import pandas as pd

    def clean(texts):
        # 作者代码的基础清洗：HTML 实体残留与反斜杠
        return [t.replace(" #39;s", "'s").replace(" quot;", '"').replace("\\", " ").replace(" #39;ll", "'ll")
                for t in texts]

    train = pd.read_csv(DATA_DIR / "agnews" / "train.csv")
    test = pd.read_csv(DATA_DIR / "agnews" / "test.csv")
    train_sentences = clean(list(train["Title"] + ". " + train["Description"]))
    test_sentences = clean(list(test["Title"] + ". " + test["Description"]))
    train_labels = [int(l) - 1 for l in train["Class Index"]]  # 1-4 转 0-3
    test_labels = [int(l) - 1 for l in test["Class Index"]]
    return train_sentences, train_labels, test_sentences, test_labels


def load_trec():
    """TREC 六分类问题类型。行格式 'DESC:moun ...'，取冒号前大写缩写为标签。"""
    inv_label_dict = {"NUM": 0, "LOC": 1, "HUM": 2, "DESC": 3, "ENTY": 4, "ABBR": 5}

    def parse(path):
        sentences, labels = [], []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                label = inv_label_dict[line.split(" ")[0].split(":")[0]]
                sentence = " ".join(line.split(" ")[1:]).strip()
                # 作者代码的基础清洗
                sentence = sentence.replace(" 's", "'s").replace("`` ", '"').replace(" ''", '"')
                sentence = sentence.replace(" ?", "?").replace(" ,", ",")
                sentences.append(sentence)
                labels.append(label)
        return sentences, labels

    train_sentences, train_labels = parse(DATA_DIR / "trec" / "train.txt")
    test_sentences, test_labels = parse(DATA_DIR / "trec" / "test.txt")
    return train_sentences, train_labels, test_sentences, test_labels


def load_dataset(name):
    """返回 (train_sentences, train_labels, test_sentences, test_labels, prompt_params)。
    prompt_params 与作者 load_dataset 中同名键逐字一致（原文 prompt 设置）。"""
    params = {"task_format": "classification", "num_tokens_to_predict": 1}
    if name == "sst2":
        train_s, train_l, test_s, test_l = load_sst2()
        params["prompt_prefix"] = ""
        params["q_prefix"] = "Review: "
        params["a_prefix"] = "Sentiment: "
        params["label_dict"] = {0: ["Negative"], 1: ["Positive"]}
        params["inv_label_dict"] = {"Negative": 0, "Positive": 1}
    elif name == "agnews":
        train_s, train_l, test_s, test_l = load_agnews()
        params["prompt_prefix"] = ("Classify the news articles into the categories of World, "
                                   "Sports, Business, and Technology.\n\n")
        params["q_prefix"] = "Article: "
        params["a_prefix"] = "Answer: "
        params["label_dict"] = {0: ["World"], 1: ["Sports"], 2: ["Business"], 3: ["Technology", "Science"]}
        # 注意作者注释：Science 也映射到类 3（inv 表从 1 开始的原版遗留）
        params["inv_label_dict"] = {"World": 0, "Sports": 1, "Business": 2, "Technology": 3, "Science": 3}
    elif name == "trec":
        train_s, train_l, test_s, test_l = load_trec()
        params["prompt_prefix"] = ("Classify the questions based on whether their answer type is a "
                                   "Number, Location, Person, Description, Entity, or Abbreviation.\n\n")
        params["q_prefix"] = "Question: "
        params["a_prefix"] = "Answer Type: "
        params["label_dict"] = {0: ["Number"], 1: ["Location"], 2: ["Person"],
                                3: ["Description"], 4: ["Entity"], 5: ["Ab"]}
        params["inv_label_dict"] = {"Number": 0, "Location": 1, "Person": 2,
                                    "Description": 3, "Entity": 4, "Ab": 5}
    else:
        raise NotImplementedError("未实现的数据集: " + name)
    return train_s, train_l, test_s, test_l, params


def construct_prompt(params, train_sentences, train_labels, test_sentence):
    """构造单条 prompt（对齐作者 utils.construct_prompt）：
    prompt_prefix + 每个训练样例 [q_prefix 句子\n a_prefix 标签\n\n] + [q_prefix 测试句子\n a_prefix[:-1]]。
    末尾不留空格（GPT 系列不希望有尾随空格）。"""
    prompt = params["prompt_prefix"]
    for s, l in zip(train_sentences, train_labels):
        prompt += params["q_prefix"]
        prompt += s + "\n"
        label_names = params["label_dict"][l]
        label_str = label_names[0] if isinstance(label_names, list) else label_names
        prompt += params["a_prefix"]
        prompt += label_str + "\n\n"
    prompt += params["q_prefix"]
    prompt += test_sentence + "\n"
    assert params["a_prefix"][-1] == " "
    return prompt + params["a_prefix"][:-1]
