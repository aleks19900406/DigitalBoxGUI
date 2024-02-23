import ctypes
import os
import sys
from collections import defaultdict
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from typing import Dict, Optional, Set, Tuple, Type

from pycparser import CParser, c_ast

from ..utils import CtypesEnum, CtypesStruct

TYPE_MAPPINGS = {
    "char": ctypes.c_char,
    "unsigned char": ctypes.c_byte,
    "int": ctypes.c_int,
    "int8_t": ctypes.c_int8,
    "uint8_t": ctypes.c_uint8,
    "int16_t": ctypes.c_int16,
    "uint16_t": ctypes.c_uint16,
    "int32_t": ctypes.c_int32,
    "uint32_t": ctypes.c_uint32,
}


class TypeExtractor(c_ast.NodeVisitor):
    def __init__(self) -> None:
        super().__init__()
        self.enums = {}
        self.structs = {}
        self._objects = defaultdict(dict)
        self._o = defaultdict(dict, {"identifier": TYPE_MAPPINGS})
        self.namespaces: Dict[str, Tuple[str, object]] = {
            n: ("identifier", n) for n in TYPE_MAPPINGS
        }

    @property
    def namespace_names(self) -> Set[str]:
        return set(self.namespaces)

    def visit_Enum(self, node):
        self._register_enum(node)

    def visit_Struct(self, node: c_ast.Struct):
        self._register_struct(node)

    def visit_Union(self, node: c_ast.Union):
        self._register_union(node)

    def visit_Typedef(self, node: c_ast.Typedef):
        typ = node.type.type
        if node.name is None:
            raise ValueError("Typedef must be named")
        if isinstance(typ, c_ast.Enum):
            if typ.values is not None:
                if typ.name is None:
                    typ.name = node.type.declname
                self._register_enum(typ)
            self.namespaces[node.name] = ("enum", typ.name)
        elif isinstance(typ, c_ast.Struct):
            if typ.decls is not None:
                if typ.name is None:
                    typ.name = node.type.declname
                self._register_struct(typ)
            self.namespaces[node.name] = ("struct", typ.name)
        elif isinstance(typ, c_ast.Union):
            # if typ. is not None:
            self._register_union(typ)
            self.namespaces[node.name] = ("union", typ.name)
        elif isinstance(typ, c_ast.IdentifierType):
            # TODO: Currently all indetifier types are defined in basic
            ...
            # print(node)
            # if node.name not in self.names:
            #    self._register_identifier_type(typ)
            # self.namespaces[node.name] = ("identifier", typ.name)

    def _register_enum(self, node: c_ast.Enum):
        self._objects["enum"][node.name] = node
        self.namespaces[f"enum {node.name}"] = ("enum", node.name)
        e = self._build_enum(node)
        self._o["enum"][node.name] = e
        return e

    def _register_struct(self, node: c_ast.Struct) -> CtypesStruct:
        self._objects["struct"][node.name] = node
        self.namespaces[f"struct {node.name}"] = ("struct", node.name)
        s = self._build_struct(node)
        self._o["struct"][node.name] = s
        return s

    def _register_union(self, node: c_ast.Union):
        self._objects["union"][node.name] = node
        self.namespaces[f"union {node.name}"] = ("union", node.name)
        u = self._build_union(node)
        self._o["union"][node.name] = u
        return u

    def _register_identifier_type(self, node: c_ast.IdentifierType):
        ...  # TODO

    @staticmethod
    def _build_enum(node: c_ast.Enum):
        if node.name is None:
            raise ValueError(f"unknown enum identifier ({node.coord})")
        previous = -1
        entries = {}
        for e in node.values.enumerators:
            if isinstance(e.value, c_ast.Constant):
                value = e.value.value
            else:
                value = e.value
            if value is not None:
                value = int(value)
                previous = value
            else:
                previous += 1
                value = previous
            entries[e.name] = value
        return type(node.name, (CtypesEnum,), entries)

    def _build_struct(self, node):
        if node.name in self._o["struct"]:
            typ = self._o["struct"][node.name]
        else:
            typ = type(node.name, (CtypesStruct,), {})
            self._o["struct"][node.name] = typ
        if node.decls is not None:
            fields = []
            for d in node.decls:
                if d.bitsize is None:
                    entry = (d.name, self._derive_type(d.type))
                else:
                    t = self._derive_type(d.type)
                    entry = (d.name, t, int(d.bitsize.value))
                fields.append(entry)
            typ._fields_ = fields
        return typ

    def _build_union(self, node: c_ast.Union):
        return type(
            node.name,
            (ctypes.Union,),
            {"_fields_": [(d.name, self._derive_type(d.type)) for d in node.decls]},
        )

    def _struct_from_node(self, node: c_ast.Struct):
        # TODO: What if name is missing?
        # TODO: Does the struct need to be stored elsewhere apart from the parent?
        typ = type(node.name, (CtypesStruct,), {})
        if node.decls is not None:
            fields = []
            for d in node.decls:
                fields.append((d.name, self._derive_type(d.type)))
            typ._fields_ = fields
        return typ

    def _derive_type(self, node):
        if isinstance(node, c_ast.PtrDecl):
            typ = self._derive_type(node.type.type)
            return ctypes.POINTER(typ)
        elif isinstance(node, c_ast.Struct):
            if (typ := self.get_ctypes_object(f"struct {node.name}")) is not None:
                return typ
            else:
                return self._struct_from_node(node)
        elif isinstance(node, c_ast.TypeDecl):
            if isinstance(typ := node.type, c_ast.IdentifierType):
                if (typ := self.get_ctypes_object(" ".join(typ.names))) is not None:
                    return typ
                else:
                    raise ValueError(f"{node.name} type is nuknown")
            elif isinstance(typ, c_ast.Struct):
                return self._register_struct(typ)
            elif isinstance(typ, c_ast.Enum):
                return self._register_enum(typ)
        elif isinstance(node, c_ast.ArrayDecl):
            return self.get_ctypes_object(" ".join(node.type.type.names)) * int(
                node.dim.value
            )

    def get_py_object(self, name: str):
        group, link = self.namespaces[name]
        object_group = self._objects.get(group, None)
        if object_group is None:
            return None
        return object_group.get(link, None)

    def get_ctypes_object(self, name: str) -> Optional[Type]:
        group, link = self.namespaces[name]
        object_group = self._o.get(group, None)
        if object_group is None:
            return None
        return object_group.get(link, None)


class TypeParser(CParser):
    """Source c file type parser"""

    def __init__(
        self,
        lex_optimize,
        lexer,
        lextab,
        yacc_optimize,
        yacctab,
        yacc_debug,
        taboutputdir,
    ):
        super().__init__(
            lex_optimize,
            lexer,
            lextab,
            yacc_optimize,
            yacctab,
            yacc_debug,
            taboutputdir,
        )
        self._type_extractor = TypeExtractor()

    def parse(self, text: str, name: str) -> ModuleType:
        """Parse source text into a python module

        :param text: string containing the C source code
        :type text: str
        :param name: desired module name
        :return: parsed module
        """
        if name in sys.modules:
            raise NameError("module with the same name is already imported")
        module_path = Path.cwd() / os.path.join(*name.split("."))
        spec = spec_from_file_location(name, module_path / "__init__.py")
        main_module = module_from_spec(spec)
        sys.modules[main_module.__name__] = main_module
        self._type_extractor.visit(super().parse(text))  # TODO: Add module
        self._populate_main_module(main_module)
        return main_module

    def _populate_main_module(self, main_module: ModuleType) -> None:
        for alias, (namespace, _) in self._type_extractor.namespaces.items():
            obj = self._type_extractor.get_ctypes_object(alias)
            if " " in alias:
                aliases = alias.split(" ")
                if aliases[0] == namespace:
                    alias = "_".join(aliases[1:])
                    module = getattr(main_module, namespace, None)
                    if module is None:
                        # TODO: clild modules' paths should be based on main module's
                        spec = spec_from_file_location(
                            f"{main_module.__name__}.{namespace}",
                            os.path.join(
                                os.getcwd(), main_module.__name__, f"{namespace}.py"
                            ),
                        )
                        module = module_from_spec(spec)
                        setattr(main_module, namespace, module)
                    if hasattr(module, alias):
                        raise NameError(
                            f"name {alias} already exists in module {module}"
                        )
                    setattr(module, alias, obj)
                else:
                    alias = alias.replace(" ", "_")
                    if hasattr(main_module, alias):
                        raise NameError(
                            f"name {alias} already exists in module {main_module}"
                        )
                    setattr(main_module, alias, obj)
            else:
                if hasattr(main_module, alias):
                    raise NameError(
                        f"name {alias} already exists in module {main_module}"
                    )
                setattr(main_module, alias, obj)
