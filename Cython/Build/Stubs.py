import ast as py_ast
from ast import unparse

cython_to_numpy_dtype = {
    # Integers
    "char": "int8",
    "signed char": "int8",
    "unsigned char": "uint8",

    "short": "int16",
    "unsigned short": "uint16",

    "int": "int32",
    "unsigned int": "uint32",

    "long": "int64",
    "unsigned long": "uint64",

    "long long": "int64",
    "unsigned long long": "uint64",

    # Floating point
    "float": "float32",
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

    def require_numpy(self) -> None:
        """
        Mark that NumPy is required for the generated stubs.
        """
        self.__numpy_required = True

    def cython_to_python_type(self, name: str) -> str:
        if name in cython_to_numpy_dtype:
            self.require_numpy()
            return cython_to_numpy_dtype[name]

        if name == 'bint':
            return 'bool'

        return None

    def generate_numpy_array_type(self, base_type: str) -> py_ast.Subscript:
        self.require_numpy()
        return py_ast.Subscript(
            value=py_ast.Attribute(
                value=py_ast.Name(id="npt", ctx=py_ast.Load()),
                attr="NDArray",
                ctx=py_ast.Load()
            ),
            slice=py_ast.Attribute(
                value=py_ast.Name(id="np", ctx=py_ast.Load()),
                attr="float64",
                ctx=py_ast.Load()
            ),
            ctx=py_ast.Load()
        )


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
