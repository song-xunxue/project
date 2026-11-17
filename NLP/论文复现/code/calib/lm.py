"""本地 GPT-2 推理封装（对齐作者仓库 utils.complete_gpt2 的输出语义）。

日期: 2026-11-03

2026-11-03
变更说明：
  1. 初版：仅实现分类所需的两条推理路径——首 token top-k 概率、回声模式末 token logprob；
     从 code/models/<名称> 加载本地权重，左填充批处理，fp32（可选 --fp16）。
"""
import numpy as np
import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer

from calib.data_utils import MODELS_DIR


class GPT2Runner:
    """单例式 GPT-2 推理器。prompt 批处理 + 左填充，输出与作者 OpenAI 风格接口等价的概率。"""

    def __init__(self, model_name, fp16=False, device=None):
        local_dir = MODELS_DIR / model_name
        if not local_dir.exists():
            raise FileNotFoundError(
                f"本地权重不存在: {local_dir}；先运行 scripts/download_models.py 下载")
        # from_pretrained: 从本地目录加载 HuggingFace 模型与分词器（不联网）
        self.tokenizer = GPT2Tokenizer.from_pretrained(local_dir)
        self.model = GPT2LMHeadModel.from_pretrained(local_dir)
        # fp16: 半精度推理（省显存提速）；默认 False 保持论文一致的 fp32
        if fp16:
            self.model = self.model.half()
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model.eval().to(self.device)
        # 左填充 + pad 取 eos：批内短序列填在左边，保证末位置都是真实最后 token
        self.tokenizer.padding_side = "left"
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.model.config.pad_token_id = self.model.config.eos_token_id
        self.model_name = model_name

    def _forward(self, prompts):
        """批量前向；返回 (input_ids, logits)。position_ids 处理与作者一致：
        按 attention_mask 重新累计位置，把填充位屏蔽为 1。
        注：transformers 5.x 已移除 batch_encode_plus，统一用 tokenizer(...) 调用。"""
        enc = self.tokenizer(prompts, return_tensors="pt", padding=True)
        input_ids = enc["input_ids"].to(self.device)
        attention_mask = enc["attention_mask"].to(self.device)
        position_ids = attention_mask.long().cumsum(-1) - 1
        position_ids.masked_fill_(attention_mask == 0, 1)
        with torch.no_grad():  # 纯推理，免建反向图（作者实现为 forward 后 detach，等价且更省显存）
            logits = self.model(input_ids=input_ids,
                                attention_mask=attention_mask,
                                position_ids=position_ids).logits
        return input_ids, logits

    def first_token_topk(self, prompts, num_log_probs=100):
        """每条 prompt 首 token 的 top-k 分布（分类标签概率的主通道）。
        返回 [{token_str: logprob, ...}, ...]，顺序与输入一致。"""
        out = []
        for i in range(0, len(prompts), self.bs):
            batch = prompts[i:i + self.bs]
            input_ids, logits = self._forward(batch)
            # 左填充下每条序列真实末 token 都在 -1 位；其 logits 即首生成 token 的分布
            probs = torch.softmax(logits[:, -1, :], dim=-1).cpu()
            top_logprobs = torch.log(probs + 1e-30)  # 防止 log(0)
            top_probs, top_tokens = torch.topk(probs, k=min(num_log_probs, probs.shape[-1]))
            for row_p, row_t, row_lp in zip(top_probs, top_tokens, top_logprobs):
                # top_logprobs: 与 OpenAI 返回一致的 {token字符串: logprob} 字典
                out.append({self.tokenizer.decode([t.item()]): lp.item()
                            for t, lp in zip(row_t, row_p)})
        return out

    def echo_last_token_logprob(self, prompts):
        """回声模式：取每条文本最后一个 token 的条件 logprob（补缺失标签与 p_cf 用）。
        输入文本应已形如 'prompt + " " + label'。"""
        out = []
        for i in range(0, len(prompts), self.bs):
            batch = prompts[i:i + self.bs]
            input_ids, logits = self._forward(batch)
            log_probs = torch.log_softmax(logits[:, :-1, :], dim=-1)  # 位置 t 预测 t+1
            # 末 token 的 logprob：用 -2 位 logits 预测 -1 位 token
            last_tokens = input_ids[:, -1]
            lp = log_probs[:, -1, :].gather(1, last_tokens.unsqueeze(1)).squeeze(1)
            out.extend(lp.cpu().tolist())
        return out

    def set_batch_size(self, bs):
        self.bs = bs
