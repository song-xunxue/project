"""
公共工具函数

李文煜 1120233042
"""

import os

# 全局结果记录
_results = []


def log(msg):
    """打印并记录结果到列表"""
    print(msg)
    _results.append(msg)


def save_results(filepath):
    """将记录的结果写入文件"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(_results))
    log(f"结果已保存: {filepath}")


def save_fig(fig, name, fig_dir):
    """
    保存图为PDF和SVG矢量格式

    参数:
        fig: matplotlib figure对象
        name: 文件名（不含扩展名）
        fig_dir: 输出目录
    """
    pdf_path = os.path.join(fig_dir, f'{name}.pdf')
    svg_path = os.path.join(fig_dir, f'{name}.svg')
    fig.savefig(pdf_path, dpi=300, bbox_inches='tight')
    fig.savefig(svg_path, format='svg', bbox_inches='tight')
    log(f"图已保存: {name}.pdf/svg")
