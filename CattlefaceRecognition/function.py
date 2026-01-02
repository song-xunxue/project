import re
from pathlib import Path
def get_next_filename(base_name='best_model', extension=None, start_num=1, digit_width=2):
    """
    获取下一个自增长文件名

    参数:
        base_name: 文件名前缀 (如 "model")
        extension: 文件扩展名 (如 "pt" 或 "csv")
        start_num: 起始编号 (默认1)
        digit_width: 数字部分的宽度 (默认2位)

    返回:
        下一个可用的文件名 (如 "model_02.pt")
    """
    # 确保文件后缀是确定的
    if extension is None:
        print("文件后缀不确定")
        return

    # 确保扩展名以点开头
    if not extension.startswith('.'):
        extension = '.' + extension

    # 创建正则表达式模式匹配文件名
    pattern = re.compile(rf'^{base_name}_\d{{{digit_width}}}{re.escape(extension)}$')

    # 获取目录下所有匹配的文件
    directory = Path('.')
    matching_files = [f for f in directory.glob('*') if pattern.match(f.name)]

    # 如果没有匹配文件，返回起始编号
    if not matching_files:
        return f"{base_name}_{start_num:0{digit_width}d}{extension}"

    # 提取现有编号并找到最大值
    max_num = start_num
    for file in matching_files:
        # 从文件名中提取数字部分
        num_str = file.stem.split('_')[-1]
        try:
            num = int(num_str)
            if num > max_num:
                max_num = num
        except ValueError:
            continue

    # 返回下一个编号的文件名
    next_num = max_num + 1
    return f"{base_name}_{next_num:0{digit_width}d}{extension}"



