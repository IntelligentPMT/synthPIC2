"""Module for parsing of boolean expressions as strings.

Based on: https://github.com/pyparsing/pyparsing/blob/master/examples/simpleBool.py
"""

from typing import Callable, Iterable

from pyparsing import infixNotation
from pyparsing import Keyword
from pyparsing import opAssoc
from pyparsing import ParserElement
from pyparsing import ParseResults

ParserElement.enablePackrat()


class BoolOperand:
    """Class to parse boolean operands."""

    def __init__(self, t: ParseResults) -> None:
        self.label = str(t[0])

        match self.label.lower():
            case "true":
                self.value = True
            case "false":
                self.value = False
            case _:
                raise ValueError(f"Unexpected value: {self.label}")

    def __bool__(self) -> bool:
        return self.value

    def __str__(self) -> str:
        return self.label

    __repr__ = __str__


class BoolNot:
    """ Class to parse `not`."""

    def __init__(self, t: ParseResults) -> None:
        self.arg = t[0][1]

    def __bool__(self) -> bool:
        v = bool(self.arg)
        return not v

    def __str__(self) -> str:
        return "~" + str(self.arg)

    __repr__ = __str__


class BoolBinOp:
    """Base class to parse binary operations."""
    repr_symbol: str = ""
    eval_fn: Callable[[Iterable[bool]], bool] = lambda _: False

    def __init__(self, t: ParseResults) -> None:
        self.args = t[0][0::2]

    def __str__(self) -> str:
        sep = f" {self.repr_symbol} "
        return "(" + sep.join(map(str, self.args)) + ")"

    def __bool__(self) -> bool:
        # mypy bug: see https://github.com/python/mypy/issues/10711
        return self.eval_fn(bool(a) for a in self.args)    #type: ignore


class BoolAnd(BoolBinOp):
    repr_symbol = "&"
    eval_fn = all


class BoolOr(BoolBinOp):
    repr_symbol = "|"
    eval_fn = any


# define keywords and simple infix notation grammar for boolean
# expressions
TRUE = Keyword("True")
FALSE = Keyword("False")
NOT = Keyword("not")
AND = Keyword("and")
OR = Keyword("or")
boolOperand = TRUE | FALSE
boolOperand.setParseAction(BoolOperand).setName("bool_operand")

# define expression, based on expression operand and
# list of operations in precedence order
boolExpr = infixNotation(
    boolOperand,
    [
        (NOT, 1, opAssoc.RIGHT, BoolNot),
        (AND, 2, opAssoc.LEFT, BoolAnd),
        (OR, 2, opAssoc.LEFT, BoolOr),
    ],
).setName("boolean_expression")

def parse_boolean_string(string: str) -> bool:
    return bool(boolExpr.parseString(string, parseAll=True)[0])
