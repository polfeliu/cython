from ast import unparse
import ast as py_ast

class StubGenerator:

    def __init__(self, error_on_missing_implementation: bool = False):
        self.error_on_missing_implementation = error_on_missing_implementation
        self.__required_imports = {
            # Library path -> {names}
        } # TODO Render imports on start of the file

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
