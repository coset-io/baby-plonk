import tkinter as tk
from tkinter import messagebox, filedialog
from compiler.program import Program
import matplotlib.pyplot as plt
from PIL import Image, ImageTk
import io
import os
import threading
from functools import lru_cache


class PlonKApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PlonK constraints generator")
        self.create_widgets()

    def create_widgets(self):
        # Add input fields and labels
        tk.Label(self.root, text="Constraint matrix (one row per constraint, e.g.):").grid(row=0, column=0)
        tk.Label(self.root, text="1 1 0 0 1\n[0,0,1,0,1]").grid(row=0, column=1, sticky="w")
        self.constraints_text = tk.Text(self.root, height=10, width=50)
        self.constraints_text.grid(row=1, column=0, columnspan=2)

        tk.Label(self.root, text="Group Order (optional, default is number of constraints):").grid(row=2, column=0)
        self.group_order_entry = tk.Entry(self.root, width=15)
        self.group_order_entry.grid(row=2, column=1)

        # Add run button
        tk.Button(self.root, text="Generate", command=self.run_program_async).grid(row=3, column=0, columnspan=2)

        # Add result text box and scrollbar
        self.result_frame = tk.Frame(self.root)
        self.result_frame.grid(row=4, column=0, columnspan=2)

        # Create vertical scrollbar
        self.scrollbar = tk.Scrollbar(self.result_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create text box for results
        self.result_text = tk.Text(self.result_frame, height=20, width=80, yscrollcommand=self.scrollbar.set)
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH)

        # Link scrollbar to text box
        self.scrollbar.config(command=self.result_text.yview)

        # Add export button
        tk.Button(self.root, text="Export", command=self.export_results).grid(row=5, column=0, columnspan=2)

        # Add validation
        self.constraints_text.bind("<KeyRelease>", self.on_constraints_change)

    def run_program(self):
        try:
            # Get user input
            constraints_input = self.constraints_text.get("1.0", tk.END).strip()
            constraints = self.parse_constraints(constraints_input)
            
            # Automatically calculate group_order (default is the number of constraints)
            default_group_order = len(constraints)
            
            # Get user-entered group_order (use default if not provided)
            group_order_input = self.group_order_entry.get().strip()
            group_order = int(group_order_input) if group_order_input else default_group_order

            # Check if group_order is less than the number of constraints
            if group_order < len(constraints):
                messagebox.showerror("Error", f"Group order must be >= {len(constraints)}")
                return

            # Create Program object
            program = Program(constraints, group_order)

            # Display results
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, f"constraints: {len(program.constraints)}\n")
            self.result_text.insert(tk.END, f"group_order: {group_order}\n\n")

            # Iterate over all constraints and display coefficients
            for i, constraint in enumerate(program.constraints):
                coeffs = program.coeffs()[i]
                # Check if coefficients are only 0, 1, or -1
                for key, value in coeffs.items():
                    if value not in {0, 1, -1}:
                        messagebox.showerror("Error", f"Invalid coefficient: {value} in constraint {i + 1}. Only 0, 1, -1 are allowed.")
                        return
                # Display coefficients
                self.result_text.insert(tk.END, f"Coefficient of constraint {i + 1}:\n")
                self.result_text.insert(tk.END, f"q_L: {coeffs['q_L']}\n")
                self.result_text.insert(tk.END, f"q_R: {coeffs['q_R']}\n")
                self.result_text.insert(tk.END, f"q_M: {coeffs['q_M']}\n")
                self.result_text.insert(tk.END, f"q_C: {coeffs['q_C']}\n")
                self.result_text.insert(tk.END, f"q_O: {coeffs['q_O']}\n\n")

                # Generate substituted LaTeX equation
                latex_eq = f"$${coeffs['q_L']} \\cdot w_a + {coeffs['q_R']} \\cdot w_b + {coeffs['q_M']} \\cdot (w_a \\cdot w_b) + {coeffs['q_C']} - {coeffs['q_O']} \\cdot w_c \\overset{{?}}{{=}} 0$$"
                self.result_text.insert(tk.END, f"LaTeX equation for constraint {i + 1}:\n")
                
                # Render LaTeX formula and display
                latex_image = self.render_latex(latex_eq)
                latex_photo = ImageTk.PhotoImage(latex_image)
                latex_label = tk.Label(self.result_text, image=latex_photo)
                latex_label.image = latex_photo  # Keep reference to avoid garbage collection
                self.result_text.window_create(tk.END, window=latex_label)
                self.result_text.insert(tk.END, "\n\n")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def on_constraints_change(self, event):
        """Handle changes in the constraints text box"""
        input_text = self.constraints_text.get("1.0", tk.END).strip()
        if self.validate_constraints(input_text):
            self.constraints_text.config(bg="white")
        else:
            self.constraints_text.config(bg="#ffcccc")

    def validate_constraints(self, input_text):
        """Validate the constraint matrix input"""
        try:
            self.parse_constraints(input_text)
            return True
        except ValueError:
            return False

    def run_program_async(self):
        threading.Thread(target=self.run_program).start()

    def export_results(self):
        """Export the results to a file"""
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if file_path:
            with open(file_path, "w") as file:
                file.write(self.result_text.get("1.0", tk.END))

    @staticmethod
    def parse_constraints(input_text):
        """Convert the user-entered constraint matrix into a two-dimensional list"""
        constraints = []
        for row in input_text.splitlines():
            row = row.strip()
            if row.startswith("[") and row.endswith("]"):
                # Process list-formatted strings (e.g. [1,1,0,0,1])
                try:
                    constraints.append(list(map(int, row[1:-1].split(","))))
                except ValueError:
                    raise ValueError(f"Invalid row format: {row}")
            else:
                # Process space-separated numbers (e.g. 1 1 0 0 1)
                try:
                    constraints.append(list(map(int, row.split())))
                except ValueError:
                    raise ValueError(f"Invalid row format: {row}")
        return constraints

    @lru_cache(maxsize=100)
    def render_latex(self, latex_str):
        """Render a LaTeX formula as an image with caching"""
        fig, ax = plt.subplots(figsize=(6, 1))
        ax.axis("off")
        plt.rcParams['text.latex.preamble'] = r'\usepackage{amsmath}'
        ax.text(0, 0.8, latex_str, fontsize=10, ha="left", va="top", usetex=True)
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.1, dpi=200)
        plt.close(fig)
        buf.seek(0)
        return Image.open(buf)


if __name__ == "__main__":
    root = tk.Tk()
    app = PlonKApp(root)
    root.mainloop()


# Enable LaTeX rendering
plt.rcParams['text.usetex'] = True
# Set LaTeX path (adjust as needed for your system)
os.environ['PATH'] += ':/Library/TeX/texbin'


