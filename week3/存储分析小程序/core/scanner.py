"""
阶段一：基础工具函数
- human_size: 字节数自适应单位
- is_hidden: 判断隐藏文件/文件夹
- _dir_size: 递归统计文件夹真实占用
- scan_directory: 扫描目录直接子项占用
- build_chart_data: 整理饼图数据（小占比合并为"其他"）
"""

import os

# 小占比合并阈值（占总大小的比例）
SMALL_RATIO_THRESHOLD = 0.01  # 1%


def human_size(num_bytes):
    """根据字节数自动选择合适的单位（B/KB/MB/GB/TB/EB）。"""
    if num_bytes < 1024:
        return f"{num_bytes} B"
    size = float(num_bytes)
    for unit in ("KB", "MB", "GB", "TB", "PB"):
        size /= 1024.0
        if size < 1024.0:
            return f"{size:.2f} {unit}"
    return f"{size:.2f} EB"


def is_hidden(path):
    """判断是否为隐藏文件/文件夹（以 . 开头，或 Windows 隐藏属性）。"""
    name = os.path.basename(path)
    if name.startswith("."):
        return True
    try:
        if os.name == "nt":
            import ctypes
            attrs = ctypes.windll.kernel32.GetFileAttributesW(path)
            if attrs != -1 and attrs & 2:  # FILE_ATTRIBUTE_HIDDEN = 2
                return True
    except Exception:
        pass
    return False


def _dir_size(path):
    """递归计算一个文件夹的总字节数，忽略隐藏项，跳过无权限项，不跟随符号链接。"""
    total = 0
    try:
        for entry in os.scandir(path):
            try:
                if is_hidden(entry.path):
                    continue
                if entry.is_dir(follow_symlinks=False):
                    total += _dir_size(entry.path)
                elif entry.is_file(follow_symlinks=False):
                    total += entry.stat().st_size
            except (PermissionError, OSError):
                continue
    except (PermissionError, OSError):
        pass
    return total


def scan_directory(root_path):
    """
    扫描目录的直接子项（子文件夹/文件）占用字节数。
    返回 dict: {子项名: 占用字节数}。无权限或出错项跳过。
    """
    result = {}
    try:
        entries = list(os.scandir(root_path))
    except (PermissionError, OSError) as e:
        # 调用方负责弹提示，这里仅返回空结果
        raise e

    for entry in entries:
        try:
            if is_hidden(entry.path):
                continue
            if entry.is_dir(follow_symlinks=False):
                result[entry.name] = _dir_size(entry.path)
            elif entry.is_file(follow_symlinks=False):
                try:
                    result[entry.name] = entry.stat().st_size
                except OSError:
                    continue
        except (PermissionError, OSError):
            continue
    return result


def build_chart_data(items):
    """
    将 {名称: 字节数} 整理成饼图数据。
    占比 < SMALL_RATIO_THRESHOLD 的项合并为"其他"。
    返回: (labels, sizes, mapping)
      labels: 扇区标签列表（可能含"其他"）
      sizes: 对应字节数列表
      mapping: label -> 原始子项名（"其他"映射为 None）
    """
    total = sum(items.values())
    if total == 0:
        return [], [], {}

    labels = []
    sizes = []
    mapping = {}
    others = 0
    for name, size in sorted(items.items(), key=lambda x: -x[1]):
        if size / total < SMALL_RATIO_THRESHOLD:
            others += size
            continue
        labels.append(name)
        sizes.append(size)
        mapping[name] = name
    if others > 0:
        labels.append("其他")
        sizes.append(others)
        mapping["其他"] = None
    return labels, sizes, mapping


if __name__ == "__main__":
    # 阶段一自检：用本脚本所在目录的上级做演示
    import sys
    test_path = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"扫描目录: {test_path}")
    items = scan_directory(test_path)
    total = sum(items.values())
    print(f"总大小: {human_size(total)} ({total} B)")
    labels, sizes, mapping = build_chart_data(items)
    print("饼图数据:")
    for lb, sz in zip(labels, sizes):
        print(f"  {lb}: {human_size(sz)} ({sz/total*100:.2f}%)")
