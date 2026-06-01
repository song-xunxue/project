"""
RepViT 模型定义，适配 Fashion-MNIST 数据集（1×28×28 灰度图）

基于 RepViT: Revisiting Mobile CNN From ViT Perspective (CVPR 2024)
原始代码来源: https://github.com/THU-MIG/RepViT

适配修改:
  - 输入通道: 3 → 1（灰度图）
  - 分类数: 1000 → 10（Fashion-MNIST 10类）
  - 使用最小模型 RepViT-M0.6（约4M参数）

李文煜 1120233042
"""

import torch
import torch.nn as nn
from timm.layers import SqueezeExcite
from timm.models.vision_transformer import trunc_normal_


def _make_divisible(v, divisor, min_value=None):
    """确保所有层的通道数可被 divisor 整除（来自 TensorFlow 官方实现）"""
    if min_value is None:
        min_value = divisor
    new_v = max(min_value, int(v + divisor / 2) // divisor * divisor)
    if new_v < 0.9 * v:
        new_v += divisor
    return new_v


class Conv2d_BN(torch.nn.Sequential):
    """卷积层 + 批归一化层组合，支持推理时融合"""

    def __init__(self, a, b, ks=1, stride=1, pad=0, dilation=1,
                 groups=1, bn_weight_init=1, resolution=-10000):
        super().__init__()
        self.add_module('c', torch.nn.Conv2d(
            a, b, ks, stride, pad, dilation, groups, bias=False))
        self.add_module('bn', torch.nn.BatchNorm2d(b))
        torch.nn.init.constant_(self.bn.weight, bn_weight_init)
        torch.nn.init.constant_(self.bn.bias, 0)

    @torch.no_grad()
    def fuse(self):
        """将 Conv2d + BatchNorm2d 融合为单个 Conv2d（推理加速）"""
        c, bn = self._modules.values()
        w = bn.weight / (bn.running_var + bn.eps)**0.5
        w = c.weight * w[:, None, None, None]
        b = bn.bias - bn.running_mean * bn.weight / \
            (bn.running_var + bn.eps)**0.5
        m = torch.nn.Conv2d(w.size(1) * self.c.groups, w.size(
            0), w.shape[2:], stride=self.c.stride, padding=self.c.padding,
            dilation=self.c.dilation, groups=self.c.groups,
            device=c.weight.device)
        m.weight.data.copy_(w)
        m.bias.data.copy_(b)
        return m


class Residual(torch.nn.Module):
    """残差连接模块，支持训练时随机丢弃（Stochastic Depth）"""

    def __init__(self, m, drop=0.):
        super().__init__()
        self.m = m
        self.drop = drop

    def forward(self, x):
        if self.training and self.drop > 0:
            return x + self.m(x) * torch.rand(x.size(0), 1, 1, 1,
                                              device=x.device).ge_(self.drop).div(1 - self.drop).detach()
        else:
            return x + self.m(x)

    @torch.no_grad()
    def fuse(self):
        """融合残差连接：将 identity 合并到卷积权重中"""
        if isinstance(self.m, Conv2d_BN):
            m = self.m.fuse()
            assert(m.groups == m.in_channels)
            identity = torch.ones(m.weight.shape[0], m.weight.shape[1], 1, 1)
            identity = torch.nn.functional.pad(identity, [1, 1, 1, 1])
            m.weight += identity.to(m.weight.device)
            return m
        elif isinstance(self.m, torch.nn.Conv2d):
            m = self.m
            assert(m.groups != m.in_channels)
            identity = torch.ones(m.weight.shape[0], m.weight.shape[1], 1, 1)
            identity = torch.nn.functional.pad(identity, [1, 1, 1, 1])
            m.weight += identity.to(m.weight.device)
            return m
        else:
            return self


class RepVGGDW(torch.nn.Module):
    """
    RepVGG 风格的深度可分离卷积（结构重参数化核心模块）

    训练时：三个并行分支（3×3 DW Conv + 1×1 DW Conv + Identity）
    推理时：融合为单个 3×3 DW Conv
    """

    def __init__(self, ed) -> None:
        super().__init__()
        self.conv = Conv2d_BN(ed, ed, 3, 1, 1, groups=ed)    # 3×3 深度卷积
        self.conv1 = torch.nn.Conv2d(ed, ed, 1, 1, 0, groups=ed)  # 1×1 深度卷积
        self.dim = ed
        self.bn = torch.nn.BatchNorm2d(ed)

    def forward(self, x):
        return self.bn((self.conv(x) + self.conv1(x)) + x)

    @torch.no_grad()
    def fuse(self):
        """将三分支结构融合为单个 3×3 深度卷积"""
        conv = self.conv.fuse()
        conv1 = self.conv1
        conv_w = conv.weight
        conv_b = conv.bias
        conv1_w = conv1.weight
        conv1_b = conv1.bias
        # 将 1×1 卷积 pad 到 3×3
        conv1_w = torch.nn.functional.pad(conv1_w, [1, 1, 1, 1])
        # Identity 分支也 pad 到 3×3
        identity = torch.nn.functional.pad(
            torch.ones(conv1_w.shape[0], conv1_w.shape[1], 1, 1, device=conv1_w.device),
            [1, 1, 1, 1])
        # 合并三个分支的权重和偏置
        final_conv_w = conv_w + conv1_w + identity
        final_conv_b = conv_b + conv1_b
        conv.weight.data.copy_(final_conv_w)
        conv.bias.data.copy_(final_conv_b)
        # 融合 BN 层
        bn = self.bn
        w = bn.weight / (bn.running_var + bn.eps)**0.5
        w = conv.weight * w[:, None, None, None]
        b = bn.bias + (conv.bias - bn.running_mean) * bn.weight / \
            (bn.running_var + bn.eps)**0.5
        conv.weight.data.copy_(w)
        conv.bias.data.copy_(b)
        return conv


class RepViTBlock(nn.Module):
    """
    RepViT 核心构建块，遵循 MetaFormer 范式

    结构: Token Mixer (空间混合) → Channel Mixer (通道混合)
    - stride=1: RepVGGDW + SE → 残差 MLP
    - stride=2: DWConv(s=2) + SE + PWConv → 残差 MLP（同时下采样）
    """

    def __init__(self, inp, hidden_dim, oup, kernel_size, stride, use_se, use_hs):
        super(RepViTBlock, self).__init__()
        assert stride in [1, 2]
        self.identity = stride == 1 and inp == oup
        assert(hidden_dim == 2 * inp)

        if stride == 2:
            # 下采样分支：DWConv(stride=2) + SE + 1×1 Conv
            self.token_mixer = nn.Sequential(
                Conv2d_BN(inp, inp, kernel_size, stride, (kernel_size - 1) // 2, groups=inp),
                SqueezeExcite(inp, 0.25) if use_se else nn.Identity(),
                Conv2d_BN(inp, oup, ks=1, stride=1, pad=0)
            )
            self.channel_mixer = Residual(nn.Sequential(
                Conv2d_BN(oup, 2 * oup, 1, 1, 0),     # 逐点扩展
                nn.GELU(),                                # GELU 激活
                Conv2d_BN(2 * oup, oup, 1, 1, 0, bn_weight_init=0),  # 逐点压缩
            ))
        else:
            # 等分辨率分支：RepVGGDW + SE → 残差 MLP
            assert(self.identity)
            self.token_mixer = nn.Sequential(
                RepVGGDW(inp),
                SqueezeExcite(inp, 0.25) if use_se else nn.Identity(),
            )
            self.channel_mixer = Residual(nn.Sequential(
                Conv2d_BN(inp, hidden_dim, 1, 1, 0),
                nn.GELU(),
                Conv2d_BN(hidden_dim, oup, 1, 1, 0, bn_weight_init=0),
            ))

    def forward(self, x):
        return self.channel_mixer(self.token_mixer(x))


class BN_Linear(torch.nn.Sequential):
    """BatchNorm1d + Linear 层组合，支持推理时融合"""

    def __init__(self, a, b, bias=True, std=0.02):
        super().__init__()
        self.add_module('bn', torch.nn.BatchNorm1d(a))
        self.add_module('l', torch.nn.Linear(a, b, bias=bias))
        trunc_normal_(self.l.weight, std=std)
        if bias:
            torch.nn.init.constant_(self.l.bias, 0)

    @torch.no_grad()
    def fuse(self):
        bn, l = self._modules.values()
        w = bn.weight / (bn.running_var + bn.eps)**0.5
        b = bn.bias - self.bn.running_mean * \
            self.bn.weight / (bn.running_var + bn.eps)**0.5
        w = l.weight * w[None, :]
        if l.bias is None:
            b = b @ self.l.weight.T
        else:
            b = (l.weight @ b[:, None]).view(-1) + self.l.bias
        m = torch.nn.Linear(w.size(1), w.size(0), device=l.weight.device)
        m.weight.data.copy_(w)
        m.bias.data.copy_(b)
        return m


class Classifier(nn.Module):
    """分类头，支持知识蒸馏（可选）"""

    def __init__(self, dim, num_classes, distillation=False):
        super().__init__()
        self.classifier = BN_Linear(dim, num_classes) if num_classes > 0 else torch.nn.Identity()
        self.distillation = distillation
        if distillation:
            self.classifier_dist = BN_Linear(dim, num_classes) if num_classes > 0 else torch.nn.Identity()

    def forward(self, x):
        if self.distillation:
            x = self.classifier(x), self.classifier_dist(x)
            if not self.training:
                x = (x[0] + x[1]) / 2
        else:
            x = self.classifier(x)
        return x

    @torch.no_grad()
    def fuse(self):
        classifier = self.classifier.fuse()
        if self.distillation:
            classifier_dist = self.classifier_dist.fuse()
            classifier.weight += classifier_dist.weight
            classifier.bias += classifier_dist.bias
            classifier.weight /= 2
            classifier.bias /= 2
            return classifier
        else:
            return classifier


class RepViT(nn.Module):
    """
    RepViT 模型主类

    适配 Fashion-MNIST:
    - 输入通道: 1（灰度图）
    - 分类数: 10
    - 空间尺寸变化: 28→14→7→4→2→1（Stem两次stride=2 + 3个stride=2 Block）

    参数:
        cfgs: 模型配置列表 [[kernel_size, expansion_ratio, channels, use_se, use_hs, stride], ...]
        in_channels: 输入通道数（1 for Fashion-MNIST）
        num_classes: 分类数（10 for Fashion-MNIST）
    """

    def __init__(self, cfgs, in_channels=1, num_classes=10):
        super(RepViT, self).__init__()
        self.cfgs = cfgs

        # Stem 层：两次 3×3 卷积 + stride=2 下采样（28→14→7）
        input_channel = self.cfgs[0][2]
        patch_embed = torch.nn.Sequential(
            Conv2d_BN(in_channels, input_channel // 2, 3, 2, 1),  # 28→14
            torch.nn.GELU(),
            Conv2d_BN(input_channel // 2, input_channel, 3, 2, 1),  # 14→7
        )
        layers = [patch_embed]

        # 构建 RepViT Block 序列
        block = RepViTBlock
        for k, t, c, use_se, use_hs, s in self.cfgs:
            output_channel = _make_divisible(c, 8)
            exp_size = _make_divisible(input_channel * t, 8)
            layers.append(block(input_channel, exp_size, output_channel, k, s, use_se, use_hs))
            input_channel = output_channel

        self.features = nn.ModuleList(layers)
        self.classifier = Classifier(output_channel, num_classes)

    def forward(self, x):
        for f in self.features:
            x = f(x)
        # 全局平均池化 → 展平 → 分类
        x = torch.nn.functional.adaptive_avg_pool2d(x, 1).flatten(1)
        x = self.classifier(x)
        return x


def repvit_m0_6(in_channels=1, num_classes=10):
    """
    构建 RepViT-M0.6 模型（最小变体，约4M参数）

    参数:
        in_channels: 输入通道数
        num_classes: 输出分类数

    返回:
        RepViT 模型实例
    """
    # 配置格式: [kernel_size, expansion_ratio, channels, use_se, use_hs, stride]
    cfgs = [
        # Stage 1: 7×7
        [3, 2, 40, 1, 0, 1],   # SE, stride=1
        [3, 2, 40, 0, 0, 1],   # 无SE, stride=1
        # Stage 2: 7→4
        [3, 2, 80, 0, 0, 2],   # 下采样 stride=2
        [3, 2, 80, 1, 0, 1],   # SE
        [3, 2, 80, 0, 0, 1],
        # Stage 3: 4→2
        [3, 2, 160, 0, 1, 2],  # 下采样 stride=2, use_hs=1
        [3, 2, 160, 1, 1, 1],
        [3, 2, 160, 0, 1, 1],
        [3, 2, 160, 1, 1, 1],
        [3, 2, 160, 0, 1, 1],
        [3, 2, 160, 1, 1, 1],
        [3, 2, 160, 0, 1, 1],
        [3, 2, 160, 1, 1, 1],
        [3, 2, 160, 0, 1, 1],
        [3, 2, 160, 0, 1, 1],
        # Stage 4: 2→1
        [3, 2, 320, 0, 1, 2],  # 下采样 stride=2
        [3, 2, 320, 1, 1, 1],
    ]
    return RepViT(cfgs, in_channels=in_channels, num_classes=num_classes)


if __name__ == '__main__':
    # 打印模型结构和参数量
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = repvit_m0_6().to(device)
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"RepViT-M0.6 (Fashion-MNIST)")
    print(f"总参数量: {total_params:,}")
    print(f"可训练参数量: {trainable_params:,}")
    # 测试前向传播
    x = torch.randn(2, 1, 28, 28).to(device)
    y = model(x)
    print(f"输入: {x.shape} → 输出: {y.shape}")
