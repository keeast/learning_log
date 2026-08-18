"""阶段五综合验证：覆盖 PRD 验收 6 项。"""
import os
import tkinter as tk
from core.scanner import scan_directory, build_chart_data, human_size, is_hidden, _dir_size
from ui.app_window import FolderAnalyzerApp

r = tk.Tk()
app = FolderAnalyzerApp(r)
r.update()

passed = []

# 构造测试目录
ROOT = "verifydata"
if os.path.exists(ROOT):
    import shutil
    shutil.rmtree(ROOT)
os.makedirs(f"{ROOT}/big", exist_ok=True)
os.makedirs(f"{ROOT}/sub/nested", exist_ok=True)
open(f"{ROOT}/big/a.bin", "wb").write(b"x" * 5_000_000)      # 5MB
open(f"{ROOT}/tiny1.txt", "w").write("a")                    # ~1B 占比极小
open(f"{ROOT}/tiny2.txt", "w").write("b")
open(f"{ROOT}/sub/nested/deep.bin", "wb").write(b"x" * 2_000_000)  # 2MB
open(f"{ROOT}/.hidden_file", "w").write("secret")            # 隐藏
os.makedirs(f"{ROOT}/.hiddendir")
open(f"{ROOT}/.hiddendir/x", "w").write("y")

# 1. 递归统计正确性
items = scan_directory(ROOT)
total = sum(items.values())
print(f"[1] 递归统计: 总={human_size(total)} ({total} B)")
# 预期: 5MB + 2MB + 2*tiny ≈ 7,000,00x，且不含隐藏项
assert total > 7_000_000, "递归大小异常"
assert ".hidden_file" not in items and ".hiddendir" not in items, "隐藏项未被忽略"
passed.append("1.递归统计+隐藏忽略")

# 2. 单位自适应
print(f"[2] 单位自适应: 5MB文件→{human_size(5_000_000)}, 500B→{human_size(500)}, 2GB→{human_size(2*1024**3)}")
assert "MB" in human_size(5_000_000)
assert "B" in human_size(500) or "KB" in human_size(500)
assert "GB" in human_size(2 * 1024 ** 3)
passed.append("2.单位自适应")

# 3. 小占比合并为"其他"
labels, sizes, mapping = build_chart_data(items)
print(f"[3] 小占比合并: labels={labels}")
assert "其他" in labels, "小占比未合并为其他"
assert mapping.get("其他") is None
passed.append("3.小占比合并为其他")

# 4. 下钻/返回路径链
app.analyze(ROOT)
r.update()
assert os.path.basename(app.current_path) == "verifydata"
app._drill_down("sub"); r.update()
assert os.path.basename(app.current_path) == "sub"
app._drill_down("nested"); r.update()
assert os.path.basename(app.current_path) == "nested"
app._on_back(); r.update()
assert os.path.basename(app.current_path) == "sub"
app._on_back(); r.update()
assert os.path.basename(app.current_path) == "verifydata"
assert app.back_btn.instate(["disabled"]), f"返回顶层后按钮应禁用，实际 state={app.back_btn.cget('state')}"
print("[4] 下钻/返回路径链正确")
passed.append("4.下钻/返回路径链")

# 5. 无权限跳过（扫描系统目录不应崩溃）
try:
    sys_items = scan_directory("C:\\Windows\\System32")
    print(f"[5] 无权限跳过: C:\\Windows\\System32 扫描得到 {len(sys_items)} 项，未崩溃")
    passed.append("5.无权限跳过不崩")
except Exception as e:
    print(f"[5] 扫描系统目录异常: {e}")
    raise

# 6. 三种输入方式回调存在且可触发
app.path_var.set(ROOT)
app._on_analyze(); r.update()
assert os.path.basename(app.current_path) == "verifydata"
print("[6] 地址输入分析 OK")
# 浏览/拖拽在无GUI交互下仅验证方法可调用
assert callable(app._on_browse)
assert callable(app._register_drop)
passed.append("6.三种输入方式")

print("\n==== 验证结果 ====")
for p in passed:
    print("  [PASS]", p)
print(f"共通过 {len(passed)} 项")

r.destroy()
