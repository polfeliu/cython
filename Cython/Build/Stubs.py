import ast as py_ast
from ast import unparse
from typing import Optional, Union

cython_to_numpy_dtype = {
    # Integers
    "char": "int8",
    "signed char": "int8",
    "unsigned char": "uint8",

    "short": "int16",
    "unsigned short": "uint16",

    # "int" Built-in python type
    "unsigned int": "uint32",

    "long": "int64",
    "unsigned long": "uint64",

    "long long": "int64",
    "unsigned long long": "uint64",

    # Floating point
    # "float" Built-in python type
    "double": "float64",
    "long double": "longdouble",

    # Complex numbers
    "float complex": "complex64",
    "double complex": "complex128",
}


class StubGenerator:

    def __init__(self, error_on_missing_implementation: bool = False):
        self.error_on_missing_implementation = error_on_missing_implementation
        self.__required_imports = {
            # Library path -> {names}
        }  # TODO Render imports on start of the file

        self.__numpy_required = False
        self.__imported_symbols = set()

    def require_import(self, library_path: str, name: str) -> py_ast.Name:
        """
        Ensure that a library is imported in the generated stubs.

        :param library_path: The path to the library to import.
        :param name: The name of the item to import.
        """
        if library_path not in self.__required_imports:
            self.__required_imports[library_path] = set()
        if name not in self.__required_imports[library_path]:
            self.__required_imports[library_path].add(name)

        return py_ast.Name(name)

    def cython_to_python_type(self, name: str) -> Union[None, py_ast.Attribute, py_ast.Name]:
        if name in cython_to_numpy_dtype:
            nptype = cython_to_numpy_dtype[name]
            self.require_import('np', nptype)
            return py_ast.Attribute(
                value='np',
                attr=nptype
            )

        if name == 'bint':
            return py_ast.Name('bool')

        return py_ast.Name(name)

    def generate_numpy_array_type(self, base_type: py_ast.Attribute) -> py_ast.Subscript:
        self.require_import('np')
        return py_ast.Subscript(
            value=py_ast.Attribute(
                value=py_ast.Name(id="npt", ctx=py_ast.Load()),
                attr="NDArray",
                ctx=py_ast.Load()
            ),
            slice=base_type,
            ctx=py_ast.Load()
        )

    def convert_declarator_and_type(self, declarator, typ, stub_gen: "StubGenerator"):
        from Cython.Compiler.Nodes import CArrayDeclaratorNode

        if isinstance(declarator, CArrayDeclaratorNode):
            return py_ast.Name(declarator.base.name), self.generate_numpy_array_type(typ.name)

        return declarator.generate_stub_node(stub_gen), typ.generate_stub_node(stub_gen)

    def register_imported_symbol(self, symbol: str):
        self.__imported_symbols.add(symbol)


def write_stubs_to_file(stub_asts, output_file: str):  # TODO Move
    """
    Write the generated stubs to a file.

    :param stub_asts: A list of AST nodes representing the generated stubs.
    :param output_file: The file path where the stubs should be written.
    """
    # Unparse the AST to source code
    unparsed_code = unparse(stub_asts)

    # Write to the output file
    with open(output_file, "w") as f:
        f.write(unparsed_code)
