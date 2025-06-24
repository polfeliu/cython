import ast

class ASTPrinter(ast.NodeVisitor):
    def __init__(self):
        self.indent = 0

    def generic_visit(self, node):
        print("#######")
        print("  " * self.indent + f"{node.__class__.__name__}: ({node})")

        for field_name, value in ast.iter_fields(node):
            print("  " * self.indent +f"-{field_name}: {value}")

        self.indent += 1
        super().generic_visit(node)
        self.indent -= 1

def parse_python_file(filename):
    with open(filename, "r") as file:
        source = file.read()
    tree = ast.parse(source, filename=filename)
    return tree



if __name__ == "__main__":

    tree = parse_python_file("example_ast.py")

    printer = ASTPrinter()
    printer.visit(tree)
