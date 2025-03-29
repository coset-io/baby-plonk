import tkinter as tk
from tkinter import messagebox
from compiler.program import Program
import matplotlib.pyplot as plt
from PIL import Image, ImageTk
import io
import os

# 启用 LaTeX 渲染
plt.rcParams['text.usetex'] = True
# 设置 LaTeX 路径
os.environ['PATH'] += ':/Library/TeX/texbin'

def parse_constraints(input_text):
    """将用户输入的约束矩阵转换为二维列表"""
    constraints = []
    for row in input_text.splitlines():
        row = row.strip()
        if row.startswith("[") and row.endswith("]"):
            # 处理列表格式的字符串（如 [1,1,0,0,1]）
            try:
                constraints.append(list(map(int, row[1:-1].split(","))))
            except ValueError:
                raise ValueError(f"Invalid row format: {row}")
        else:
            # 处理空格分隔的数字（如 1 1 0 0 1）
            try:
                constraints.append(list(map(int, row.split())))
            except ValueError:
                raise ValueError(f"Invalid row format: {row}")
    return constraints

def render_latex(latex_str):
    """将 LaTeX 公式渲染为图像"""
    fig, ax = plt.subplots(figsize=(6, 1))
    ax.axis("off")
    # 将 amsmath 宏包放在导言区
    plt.rcParams['text.latex.preamble'] = r'\usepackage{amsmath}'
    ax.text(0, 0.8, latex_str, fontsize=10, ha="left", va="top", usetex=True)
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.1, dpi=200)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf)

def run_program():
    try:
        # 获取用户输入
        constraints_input = constraints_text.get("1.0", tk.END).strip()
        constraints = parse_constraints(constraints_input)
        
        # 自动计算 group_order（默认值为约束数量的最大值）
        default_group_order = len(constraints)
        
        # 获取用户输入的 group_order（如果未输入，使用默认值）
        group_order_input = group_order_entry.get().strip()
        group_order = int(group_order_input) if group_order_input else default_group_order

        # 检查 group_order 是否小于约束数量
        if group_order < len(constraints):
            messagebox.showerror("Error", f"Group order must be >= {len(constraints)}")
            return

        # 创建 Program 对象
        program = Program(constraints, group_order)

        # 显示结果
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, f"constraints: {len(program.constraints)}\n")
        result_text.insert(tk.END, f"group_order: {group_order}\n\n")

        # 遍历所有约束并显示系数
        for i, constraint in enumerate(program.constraints):
            coeffs = program.coeffs()[i]
            # 检查系数是否只能是 0, 1, -1
            for key, value in coeffs.items():
                if value not in {0, 1, -1}:
                    messagebox.showerror("Error", f"Invalid coefficient: {value} in constraint {i + 1}. Only 0, 1, -1 are allowed.")
                    return
            # 显示系数
            result_text.insert(tk.END, f"Coefficient of constraint {i + 1}:\n")
            result_text.insert(tk.END, f"q_L: {coeffs['q_L']}\n")
            result_text.insert(tk.END, f"q_R: {coeffs['q_R']}\n")
            result_text.insert(tk.END, f"q_M: {coeffs['q_M']}\n")
            result_text.insert(tk.END, f"q_C: {coeffs['q_C']}\n")
            result_text.insert(tk.END, f"q_O: {coeffs['q_O']}\n\n")

            # 生成代入后的 LaTeX 等式
            latex_eq = f"$${coeffs['q_L']} \\cdot w_a + {coeffs['q_R']} \\cdot w_b + {coeffs['q_M']} \\cdot (w_a \\cdot w_b) + {coeffs['q_C']} - {coeffs['q_O']} \\cdot w_c \\overset{{?}}{{=}} 0$$"
            result_text.insert(tk.END, f"LaTeX equation for constraint {i + 1}:\n")
            
            # 渲染 LaTeX 公式并显示
            latex_image = render_latex(latex_eq)
            latex_photo = ImageTk.PhotoImage(latex_image)
            latex_label = tk.Label(result_text, image=latex_photo)
            latex_label.image = latex_photo  # 保持引用，避免被垃圾回收
            result_text.window_create(tk.END, window=latex_label)
            result_text.insert(tk.END, "\n\n")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# 创建主窗口
root = tk.Tk()
root.title("PlonK constraints generator")

# 添加输入框和标签
tk.Label(root, text="constraint matrix (one row per constraint, e.g.):").grid(row=0, column=0)
tk.Label(root, text="1 1 0 0 1\n[0,0,1,0,1]").grid(row=0, column=1, sticky="w")
constraints_text = tk.Text(root, height=10, width=50)
constraints_text.grid(row=1, column=0, columnspan=2)

tk.Label(root, text="Group Order (optional, default is number of constraints):").grid(row=2, column=0)
group_order_entry = tk.Entry(root, width=15)
group_order_entry.grid(row=2, column=1)

# 添加运行按钮
tk.Button(root, text="Generate", command=run_program).grid(row=3, column=0, columnspan=2)

# 添加结果文本框和滚动条
result_frame = tk.Frame(root)
result_frame.grid(row=4, column=0, columnspan=2)

# 创建垂直滚动条
scrollbar = tk.Scrollbar(result_frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# 创建结果文本框
result_text = tk.Text(result_frame, height=20, width=80, yscrollcommand=scrollbar.set)
result_text.pack(side=tk.LEFT, fill=tk.BOTH)

# 将滚动条与文本框关联
scrollbar.config(command=result_text.yview)

# 运行主循环
root.mainloop()