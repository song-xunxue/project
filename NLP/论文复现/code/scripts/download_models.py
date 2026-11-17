"""下载 GPT-2 四个规格的本地权重到 code/models/（经 hf-mirror.com 国内镜像）。

日期: 2026-11-03

2026-11-03
变更说明：
  1. 初版：snapshot_download 只取 safetensors 权重与配置/分词文件（跳过重复的 .bin），
     下载完成后打印各文件大小与 SHA256（供 data/README 与最终包校验信息使用）。
"""
import hashlib
import os
import sys
from pathlib import Path

# 国内镜像（HuggingFace 直连不稳）。代理启动时也可删掉这行直连。
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
# 镜像不代理 Xet 存储协议（其 token 接口直连 huggingface.co 会 404），禁用后走普通 HTTP
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")

from huggingface_hub import snapshot_download  # noqa: E402  需在设置环境变量之后导入

CODE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = CODE_DIR / "models"

# 四个规格：124M / 355M / 774M / 1.5B（论文 Table 4 对应 gpt2-xl）
MODELS = ["gpt2", "gpt2-medium", "gpt2-large", "gpt2-xl"]
# 只要必要文件（精确名单，避开 onnx/ 子目录与 pytorch_model.bin 重复权重）
PATTERNS = ["config.json", "generation_config.json", "merges.txt", "vocab.json",
            "tokenizer.json", "tokenizer_config.json", "special_tokens_map.json",
            "model.safetensors"]


def sha256(path, block=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(block), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    names = sys.argv[1:] or MODELS
    for name in names:
        print(f"下载 {name} -> {MODELS_DIR / name}")
        snapshot_download(repo_id=name, local_dir=MODELS_DIR / name,
                          allow_patterns=PATTERNS, max_workers=4)
    print("\n=== 已就绪文件与 SHA256（前 16 位） ===")
    for name in names:
        total = 0
        for p in sorted((MODELS_DIR / name).glob("*")):
            if p.is_file():
                size = p.stat().st_size
                total += size
                print(f"{name}/{p.name}  {size / 1024**2:.1f} MB  {sha256(p)[:16]}")
        print(f"[{name}] 合计 {total / 1024**3:.2f} GB")


if __name__ == "__main__":
    main()
