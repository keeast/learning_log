"""测试当前 VSCode 的 Python 环境。"""

import sys
import platform
import importlib


def test_interpreter():
    print("=" * 50)
    print("1. 解释器信息")
    print("=" * 50)
    print(f"Python 版本 : {sys.version}")
    print(f"版本号      : {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print(f"可执行文件  : {sys.executable}")
    print(f"平台        : {platform.platform()}")
    print(f"处理器架构  : {platform.machine()}")


def test_standard_lib():
    print("\n" + "=" * 50)
    print("2. 标准库功能测试")
    print("=" * 50)
    # json
    import json
    data = {"name": "VSCode", "lang": "Python"}
    assert json.loads(json.dumps(data)) == data
    print("[OK] json 序列化/反序列化正常")
    # os / pathlib
    import os
    from pathlib import Path
    print(f"[OK] os.getcwd() = {os.getcwd()}")
    # datetime
    from datetime import datetime
    print(f"[OK] 当前时间 = {datetime.now().isoformat()}")
    # math
    import math
    print(f"[OK] math.pi = {math.pi}")


def test_third_party(packages):
    print("\n" + "=" * 50)
    print("3. 第三方库测试")
    print("=" * 50)
    for pkg in packages:
        try:
            mod = importlib.import_module(pkg)
            version = getattr(mod, "__version__", "未知")
            print(f"[OK] {pkg} 已安装，版本: {version}")
        except ImportError:
            print(f"[X] {pkg} 未安装")


def test_numpy():
    print("\n" + "=" * 50)
    print("4. NumPy 基础运算测试")
    print("=" * 50)
    try:
        import numpy as np
        a = np.array([1, 2, 3, 4, 5])
        b = np.array([10, 20, 30, 40, 50])
        print(f"数组 a = {a}")
        print(f"数组 b = {b}")
        print(f"a + b = {a + b}")
        print(f"a 的均值 = {a.mean()}")
        print(f"a 与 b 的点积 = {np.dot(a, b)}")
        print("[OK] NumPy 计算正常")
    except ImportError:
        print("[X] NumPy 未安装，跳过测试")


def main():
    test_interpreter()
    test_standard_lib()
    test_third_party(["numpy", "pandas", "matplotlib", "torch", "PIL", "requests"])
    test_numpy()
    print("\n" + "=" * 50)
    print("所有环境测试完成 [DONE]")
    print("=" * 50)


if __name__ == "__main__":
    main()
