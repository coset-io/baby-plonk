from utils import *
from .utils import *
from typing import Optional
from dataclasses import dataclass


@dataclass
class GateWires:
    """Variable names for Left, Right, and Output wires."""

    L: Optional[str]
    R: Optional[str]
    O: Optional[str]

    def as_list(self) -> list[Optional[str]]:
        return [self.L, self.R, self.O]


@dataclass
class Gate:
    """Gate polynomial"""

    L: Scalar
    R: Scalar
    M: Scalar
    O: Scalar
    C: Scalar


@dataclass
class AssemblyEqn:
    """Assembly equation mapping wires to coefficients."""

    wires: GateWires
    coeffs: dict[Optional[str], int]

    def L(self) -> Scalar:
        return Scalar(-self.coeffs.get(self.wires.L, 0))

    def R(self) -> Scalar:
        if self.wires.R != self.wires.L:
            return Scalar(-self.coeffs.get(self.wires.R, 0))
        return Scalar(0)

    def C(self) -> Scalar:
        return Scalar(-self.coeffs.get("", 0))

    def O(self) -> Scalar:
        return Scalar(self.coeffs.get("$output_coeff", 1))

    def M(self) -> Scalar:
        if None not in self.wires.as_list():
            return Scalar(
                -self.coeffs.get(get_product_key(self.wires.L, self.wires.R), 0)
            )
        return Scalar(0)

    def gate(self) -> Gate:
        return Gate(self.L(), self.R(), self.M(), self.O(), self.C())


# Converts a arithmetic expression containing numbers, variables and {+, -, *}
# into a mapping of term to coefficient
#
# For example:
# ['a', '+', 'b', '*', 'c', '*', '5'] becomes {'a': 1, 'b*c': 5}
#
# Note that this is a recursive algo, so the input can be a mix of tokens and
# mapping expressions
#
def evaluate(exprs: list[str], first_is_negative=False) -> dict[Optional[str], int]:
    # Splits by + and - first, then *, to follow order of operations
    # The first_is_negative flag helps us correctly interpret expressions
    # like 6000 - 700 - 80 + 9 (that's 5229)
    if "+" in exprs:
        L = evaluate(exprs[: exprs.index("+")], first_is_negative)
        R = evaluate(exprs[exprs.index("+") + 1 :], False)
        return {x: L.get(x, 0) + R.get(x, 0) for x in set(L.keys()).union(R.keys())}
    elif "-" in exprs:
        L = evaluate(exprs[: exprs.index("-")], first_is_negative)
        R = evaluate(exprs[exprs.index("-") + 1 :], True)
        return {x: L.get(x, 0) + R.get(x, 0) for x in set(L.keys()).union(R.keys())}
    elif "*" in exprs:
        L = evaluate(exprs[: exprs.index("*")], first_is_negative)
        R = evaluate(exprs[exprs.index("*") + 1 :], first_is_negative)
        o = {}
        for k1 in L.keys():
            for k2 in R.keys():
                o[get_product_key(k1, k2)] = L[k1] * R[k2]
        return o
    elif len(exprs) > 1:
        raise Exception("No ops, expected sub-expr to be a unit: {}".format(exprs[1]))
    elif exprs[0][0] == "-":
        return evaluate([exprs[0][1:]], not first_is_negative)
    elif exprs[0].isnumeric():
        return {"": int(exprs[0]) * (-1 if first_is_negative else 1)}
    elif is_valid_variable_name(exprs[0]):
        return {exprs[0]: -1 if first_is_negative else 1}
    else:
        raise Exception("ok wtf is {}".format(exprs[0]))


# Converts an equation to a mapping of term to coefficient, and verifies that
# the operations in the equation are valid.
#
# Also outputs a triple containing the L and R input variables and the output
# variable
#
# Think of the list of (variable triples, coeffs) pairs as this language's
# version of "assembly"
#
# Example valid equations, and output:
# a === 9                      ([None, None, 'a'], {'': 9})
# b <== a * c                  (['a', 'c', 'b'], {'a*c': 1})
# d <== a * c - 45 * a + 987   (['a', 'c', 'd'], {'a*c': 1, 'a': -45, '': 987})
#
# Example invalid equations:
# 7 === 7                      # Can't assign to non-variable
# a <== b * * c                # Two times signs in a row
# e <== a + b * c * d          # Multiplicative degree > 2
#
def eq_to_assembly(eq: list) -> AssemblyEqn:
    """将矩阵转换为 AssemblyEqn"""
    if len(eq) != 5:
        raise ValueError("Matrix must have exactly 5 elements")
    q_L, q_R, q_M, q_C, q_O = eq
    coeffs = {
        "q_L": q_L,
        "q_R": q_R,
        "q_M": q_M,
        "q_C": q_C,
        "q_O": q_O
    }
    return AssemblyEqn(GateWires(None, None, None), coeffs)
    