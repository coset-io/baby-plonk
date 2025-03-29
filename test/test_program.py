import unittest
from compiler.program import Program


class TestProgram(unittest.TestCase):
    def setUp(self):
        """初始化一些测试数据"""     
        # 矩阵格式
        self.matrix_constraints = [
            [1, 1, 0, 0, 1],  # q_L=1, q_R=1, q_M=0, q_C=0, q_O=1
            [0, 0, 1, 0, 1]   # q_L=0, q_R=0, q_M=1, q_C=0, q_O=1
        ]
        self.group_order = 4


    def test_from_numeric_constraints(self):
        """测试直接使用 q_L, q_R, q_M, q_C, q_O 的输入"""
        constraints = [
            [1, 1, 0, 0, 1],  # q_L=1, q_R=0, q_M=1, q_C=0, q_O=1
            [0, 0, 1, 0, 1], # q_L=0, q_R=1, q_M=0, q_C=1, q_O=-1
            [0, 0, 1, 0, 1], # 约束 3
            [0, 0, 1, 0, 1]  # 约束 4
        ]
        program = Program(constraints, 4)  # ✅ 这里 group_order 维持 4（表示支持 4 个约束）
        
        self.assertEqual(len(program.constraints), 4)  # ✅ 这里改成 4，因为我们有 4 个等式
        self.assertEqual(program.coeffs()[0], {'q_L': 1, 'q_R': 1, 'q_M': 0, 'q_C': 0, 'q_O': 1})  # 约束 1
        self.assertEqual(program.coeffs()[1], {'q_L': 0, 'q_R': 0, 'q_M': 1, 'q_C': 0, 'q_O': 1})  # 约束 2
        self.assertEqual(program.coeffs()[2], {'q_L': 0, 'q_R': 0, 'q_M': 1, 'q_C': 0, 'q_O': 1})  # 约束 3
        self.assertEqual(program.coeffs()[3], {'q_L': 0, 'q_R': 0, 'q_M': 1, 'q_C': 0, 'q_O': 1})  # 约束 4

if __name__ == "__main__":
    unittest.main()