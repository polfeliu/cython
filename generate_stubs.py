import ast
import json

from Cython.Build.Stubs import StubGenerator
from Cython.Compiler.Nodes import StatListNode, Node
from Cython.Compiler.TreeFragment import TreeFragment
from Cython.Compiler.Visitor import VisitorTransform
import sys
from ast import unparse
import ast as py_ast
import pprint

def parse_cython_code(code: str):
    # Parse the code into a TreeFragment
    fragment = TreeFragment(code)
    return fragment


class SimpleASTPrinter(VisitorTransform):
    def __init__(self):
        self.indent = 0
        super().__init__()

    def visit_Node(self, node):
        print("#######")
        print("  " * self.indent + f"{node.__class__.__name__}: ({node})")

        for field_name in node.child_attrs:
            value = getattr(node, field_name)
            print("  " * self.indent + f"-{field_name}: {value}")

        self.indent += 1
        self.visitchildren(node)
        self.indent -= 1

        return node


def deep_print(obj, indent=0):
    padding = '  ' * indent
    if isinstance(obj, dict):
        for k, v in obj.items():
            print(f"{padding}{k}:")
            deep_print(v, indent + 1)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            print(f"{padding}[{i}]:")
            deep_print(item, indent + 1)
    elif hasattr(obj, '__dict__'):
        print(f"{padding}{obj.__class__.__name__}:")
        deep_print(vars(obj), indent + 1)
    else:
        print(f"{padding}{repr(obj)}")

if __name__ == "__main__":  # TODO Merge to a utility argument
    if len(sys.argv) != 3:
        print("Usage: python parse_cython_ast.py <file.pyx> <file.pyi>")
        sys.exit(1)

    input = sys.argv[1]
    output = sys.argv[2]

    with open(input, "r") as f:
        code = f.read()

    tree = parse_cython_code(code)
    #SimpleASTPrinter().visit(tree.root)
    deep_print(tree.root)

    #stub_ast = tree.generate_stubs(StubGenerator(error_on_missing_implementation=True))
    #print(ast.dump(stub_ast, indent=2))

    #SimpleASTPrinter().visit(stub_ast.root)
    #stub_ast = ast.fix_missing_locations(stub_ast)
    #unparsed = unparse(stub_ast)

    #with open(output, "w") as f:
    #    f.write(unparsed)
