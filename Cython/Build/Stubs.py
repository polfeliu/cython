import ast
import ast as py_ast
from ast import unparse
from typing import Union, Iterator, Optional


class StubGenerationConfig:
    def __init__(self, error_on_missing_implementation: bool = False):
        self.error_on_missing_implementation = error_on_missing_implementation


class FileStubGenerator:
    CYTHON_TO_NUMPY_TYPES = {
        # Integers
        "char": "int8",
        "signed char": "int8",
        "unsigned char": "uint8",
        "int8_t": "int8",
        "uint8_t": "uint8",

        "short": "int16",
        "unsigned short": "uint16",
        "int16_t": "int16",
        "uint16_t": "uint16",

        # "int" Built-in python type
        "unsigned int": "uint32",
        "int32_t": "int32",
        "uint32_t": "uint32",

        "long": "int64",
        "unsigned long": "uint64",
        "int64_t": "int64",
        "uint64_t": "uint64",

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

    LIBC_TYPES_TO_PYTHON = {
        'int8_t': 'int', 'int16_t': 'int', 'int32_t': 'int', 'int64_t': 'int',
        'uint8_t': 'int', 'uint16_t': 'int', 'uint32_t': 'int', 'uint64_t': 'int',
        'int_least8_t': 'int', 'int_least16_t': 'int', 'int_least32_t': 'int', 'int_least64_t': 'int',
        'uint_least8_t': 'int', 'uint_least16_t': 'int', 'uint_least32_t': 'int', 'uint_least64_t': 'int',
        'int_fast8_t': 'int', 'int_fast16_t': 'int', 'int_fast32_t': 'int', 'int_fast64_t': 'int',
        'uint_fast8_t': 'int', 'uint_fast16_t': 'int', 'uint_fast32_t': 'int', 'uint_fast64_t': 'int',
        'intmax_t': 'int', 'uintmax_t': 'int',
    }

    def __init__(self, config: StubGenerationConfig):
        self.config = config
        # Imports required by the stubs generation.
        self._required_imports: dict[str, set[tuple[str, str]]] = {
            # Library path -> set((name, asname), ...)
        }

        # Set of python symbols detected as imported in the pyx
        self._imported_symbols = set()

        # C type aliases to be defined in the stubs.
        self.c_alias_definitions: dict[str, set[str]] = {
            # py_type -> set(c_type alias, ...)
        }

        # Set of C symbols imported in the stubs.
        # May be promoted to a c alias definition if annotation requires it.
        self.declared_c_symbols = set()


    def require_import(self, library_path: str, name: str, asname: Optional[str] = None) -> py_ast.Name:
        """
        Ensure that a library is imported in the generated stubs.

        :param library_path: The path to the library to import.
        :param name: The name of the item to import.
        :param asname: The alias to use for the imported item.
        """
        if library_path not in self._required_imports:
            self._required_imports[library_path] = set()
        if name not in self._required_imports[library_path]:
            self._required_imports[library_path].add((name, asname))

        return py_ast.Name(name if not asname else asname, ctx=py_ast.Load())

    def cython_to_python_type(self, name: str) -> Union[None, py_ast.Attribute, py_ast.Name]:
        if name in self.CYTHON_TO_NUMPY_TYPES:
            nptype = self.CYTHON_TO_NUMPY_TYPES[name]

            return py_ast.Attribute(
                value=self.require_import(None, name='numpy', asname='np'),
                attr=nptype
            )

        if name == 'bint':
            return py_ast.Name('bool')

        if name in self.declared_c_symbols:
            # Create Any alias for the C definition
            self.require_import('typing', 'Any')
            self.__add_c_alias(py_type='Any', name=name)

        return py_ast.Name(name)

    def generate_numpy_array_type(self, base_type: Union[py_ast.Attribute, str]) -> py_ast.Subscript:
        if isinstance(base_type, str):
            base_type = self.cython_to_python_type(base_type)
        return py_ast.Subscript(
            value=py_ast.Attribute(
                value=self.require_import('numpy', name='typing', asname='npt'),
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
        self._imported_symbols.add(symbol)

    def __generate_imports(self) -> Iterator[py_ast.AST]:
        for lib_path, imports in self._required_imports.items():
            names = []
            for name, asname in imports:
                imported_name = asname
                if asname is None:
                    imported_name = name

                if imported_name in self._imported_symbols:
                    continue
                names.append(py_ast.alias(name=name, asname=asname))

            if len(names) == 0:
                continue

            if lib_path is None:
                yield py_ast.Import(names)
            else:
                yield py_ast.ImportFrom(module=lib_path, names=names, level=0)

    def require_libc_alias(self, name: str, asname: Optional[str] = None):
        """Require a libc type alias to be defined in the stubs.

        :param name: Name of the libc type to alias.
        :param asname: Name of the libc type used on the file
        :return:
        """
        if name not in self.LIBC_TYPES_TO_PYTHON:
            # Unknown libc type, we cannot generate an alias for it.
            return
        py_type = self.LIBC_TYPES_TO_PYTHON[name]

        self.__add_c_alias(py_type, name if asname is None else asname)

    def __add_c_alias(self, py_type: str, name: str):
        if py_type not in self.c_alias_definitions:
            self.c_alias_definitions[py_type] = set()

        self.c_alias_definitions[py_type].add(name)

    def __generate_c_aliases(self) -> Iterator[py_ast.AST]:
        """
        Generate the c type aliases for the stubs.

        :return: An iterator of AST nodes representing the libc type aliases.
        """
        for py_type, aliases in self.c_alias_definitions.items():
            if len(aliases) == 0:
                continue

            yield py_ast.Assign(
                targets=[py_ast.Name(alias, ctx=py_ast.Store()) for alias in aliases],
                value=py_ast.Name(py_type, ctx=py_ast.Load())
            )

    def inject_code(self, stub_ast: py_ast.Module):
        """
        Inject the required imports into the given AST module.

        :param stub_ast: The AST module to inject imports into.
        :return: The modified AST module with imports injected.
        """
        for alias in self.__generate_c_aliases():
            stub_ast.body.insert(0, alias)

        for imp in self.__generate_imports():
            stub_ast.body.insert(0, imp)

    def convert_type_to_const(self, typ: py_ast.AST) -> py_ast.Constant:
        """Convert a Python AST node to a constant.

        Some types might be defined as variables in the stubs,
        Converting them to constants allows to define in any order.
        """
        if isinstance(typ, py_ast.Constant):
            return typ
        return py_ast.Constant(ast.unparse(typ))



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
