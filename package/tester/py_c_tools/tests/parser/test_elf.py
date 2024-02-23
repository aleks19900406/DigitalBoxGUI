import ctypes
from io import TextIOWrapper
from pathlib import Path
from itertools import chain
from typing import cast
from unittest import TestCase
from elftools.dwarf.die import DIE

from elftools.elf.elffile import ELFFile

from c_tools.parser.elf import (
    ArrayType,
    BaseType,
    DependencyGraph,
    DependentType,
    EntryMeta,
    EnumerationType,
    Entry,
    PointerType,
    StructureType,
    Subprogram,
    Typeable,
    Typedef,
    UnionType,
    Variable,
    die2hash,
    die_name2class_name,
    get_linked_die,
    get_linked_type,
)


class _ElfTestBase(TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).parent / "data" / "elf_test.elf"
        cls.file = path.open("rb")
        cls.elf = ELFFile(cls.file)

    @classmethod
    def tearDownClass(cls) -> None:
        if not (file := getattr(cls, "file", None)):
            return
        if not isinstance(file, TextIOWrapper):
            return
        file.close()

    @classmethod
    def _iter_die(cls, die: DIE) -> DIE:
        yield die
        for child in die.iter_children():
            yield from cls._iter_die(child)

    def _find_die_by_tag_and_name(self, die: DIE, tag: str, name: str):
        for child in self._iter_die(die):
            if child.tag == tag:
                attrs = child.attributes
                if (
                    attr := attrs.get("DW_AT_name", None)
                ) and attr.value.decode() == name:
                    return child
        self.fail(f"Invalid elf file present; missing {tag} with name {name}")

    def _find_die_by_tag(self, die: DIE, tag: str):
        for child in self._iter_die(die):
            if child.tag == tag:
                return child
        self.fail(f"Invalid elf file present; missing {tag}")

    @classmethod
    def _get_top_die(cls):
        cu = next(cls.elf.get_dwarf_info().iter_CUs())
        return cu.get_top_DIE()


class TestCallables(_ElfTestBase):
    def test_01_die2hash(self):
        hashes = []
        for _ in range(2):
            hashes.append(die2hash(self._get_top_die()))
        self.assertEqual(hashes[0], hashes[1], "Hashes of the same DIE should be equal")

    def test_02_get_linked_die(self):
        cu_die = self._get_top_die()
        typedef = self._find_die_by_tag_and_name(cu_die, "DW_TAG_typedef", "week")
        enum = get_linked_die(typedef)
        self.assertEqual(enum.tag, "DW_TAG_enumeration_type")

    def test_03_get_linked_type(self):
        cu_die = self._get_top_die()
        typedef = self._find_die_by_tag_and_name(cu_die, "DW_TAG_typedef", "week")
        enum = get_linked_type(typedef, self.elf)
        self.assertIsInstance(enum, EnumerationType, "Invalid type")
        self.assertEqual(enum.name, "_day", "Invalid enumeration")

    def test_04_die_name2class_name(self):
        bytes_name = b"some_type_name"
        str_name = bytes_name.decode()
        class_name = "SomeTypeName"
        self.assertEqual(
            die_name2class_name(bytes_name), class_name, "Invalid class name"
        )
        self.assertEqual(
            die_name2class_name(str_name), class_name, "Invalid class name"
        )


class TestEntries(_ElfTestBase):
    @staticmethod
    def _char_array2str(array: ctypes.Array) -> str:
        return bytes(array).split(b"\0")[0].decode()

    @classmethod
    def _typeable2str(cls, typeable: Typeable) -> str:
        if isinstance(typeable, DependentType):
            s = "\n".join(cls._typeable2str(i) for i in typeable.get_dependencies())
        else:
            s = ""
        return "\n".join(
            chain(
                (s,),
                (f"import {i}" for i in typeable.get_python_imports()),
                (typeable.to_python_code(),),
            )
        )

    @classmethod
    def _exec_python_code(cls, typeable: Typeable) -> None:
        exec(cls._typeable2str(typeable), {})

    def test_01_registered_types(self):
        registered_types = EntryMeta._type_lookup.keys()
        diff = {
            "DW_TAG_volatile_type",  # Should redirect to linked type
            "DW_TAG_const_type",  # Should redirect to linked type
            "DW_TAG_base_type",  # Base types
            "DW_TAG_pointer_type",  # Pointers
            "DW_TAG_enumeration_type",  # Enums
            "DW_TAG_typedef",  # Typedefs
            "DW_TAG_array_type",  # Arrays
            "DW_TAG_structure_type",  # Structs
            "DW_TAG_union_type",  # Unions
            "DW_TAG_subroutine_type",  # Function prototype declrations
            "DW_TAG_variable",  # Variables
            "DW_TAG_subprogram",  # Function definitions
        }.symmetric_difference(registered_types)
        self.assertEqual(len(diff), 0, "Some types missing")

    def test_02_getter(self):
        cu_die = self._get_top_die()
        typedef_die = self._find_die_by_tag_and_name(cu_die, "DW_TAG_typedef", "week")
        typedef = Entry.get(typedef_die, self.elf)
        self.assertIsInstance(typedef, Typedef, "Invalid type returned")
        typedef_die2 = self._find_die_by_tag_and_name(cu_die, "DW_TAG_typedef", "week")
        typedef2 = Entry.get(typedef_die2, self.elf)
        self.assertIs(typedef, typedef2, "Getter should return the same instance")

    def test_03_base_type(self):
        types = {
            "signed char": ctypes.c_int8,
            "unsigned char": ctypes.c_uint8,
            "short int": ctypes.c_int16,
            "short unsigned int": ctypes.c_uint16,
            "int": ctypes.c_int32,
            "unsigned int": ctypes.c_uint32,
            "long long int": ctypes.c_int64,
            "long long unsigned int": ctypes.c_uint64,
        }
        cu_die = self._get_top_die()
        for name, t in types.items():
            base_die = self._find_die_by_tag_and_name(cu_die, "DW_TAG_base_type", name)
            base_type = Entry.get(base_die, self.elf)
            self.assertIsInstance(base_type, BaseType, "Invalid entry type")
            self.assertEqual(t._type_, base_type.to_ctype()._type_)
            try:
                self._exec_python_code(base_type)
            except Exception:
                self.fail("BaseType does not produce executable python code")

    def test_04_pointer_type(self):
        cu_die = self._get_top_die()
        pointer_die = self._find_die_by_tag(cu_die, "DW_TAG_pointer_type")
        pointer_type = cast(PointerType, Entry.get(pointer_die, self.elf))
        self.assertIsInstance(pointer_type, PointerType, "Invalid entry type")
        self.assertEqual(
            pointer_type.to_ctype()._type_,
            ctypes.c_size_t._type_,
            "Invalid pointer integral type",
        )
        associated_type = pointer_type.associated_type
        self.assertIsInstance(associated_type, StructureType, "Invalid associated type")
        self.assertEqual(
            pointer_type.associated_type.name, "wish", "Invalid associated type"
        )
        try:
            code = "\n".join(
                chain(
                    (f"import {i}" for i in pointer_type.get_python_imports()),
                    (pointer_type.to_python_code(),),
                )
            )
            exec(
                code,
                {},
            )
        except Exception:
            self.fail("PointerType does not produce executable python code")

    def test_05_enumeration_type(self):
        cu_die = self._get_top_die()
        enumeration_die = self._find_die_by_tag_and_name(
            cu_die, "DW_TAG_enumeration_type", "_day"
        )
        enumeration_type = Entry.get(enumeration_die, self.elf)
        self.assertIsInstance(enumeration_type, EnumerationType, "Invalid entry type")
        self.assertEqual(
            enumeration_type.to_ctype()._type_, "B", "Invalid enum integral type"
        )
        try:
            self._exec_python_code(enumeration_type)
        except Exception:
            self.fail("EnumerationType does not produce executable python code")

    def test_06_typedef(self):
        cu_die = self._get_top_die()
        typedef_die = self._find_die_by_tag_and_name(cu_die, "DW_TAG_typedef", "week")
        typedef_type = cast(Typedef, Entry.get(typedef_die, self.elf))
        self.assertIsInstance(typedef_type, Typedef, "Invalid entry type")
        self.assertIsInstance(
            typedef_type.associated_type, EnumerationType, "Invalid associated type"
        )
        self.assertEqual(
            typedef_type.associated_type.name, "_day", "Invalid associated type"
        )
        try:
            self._exec_python_code(typedef_type)
        except Exception:
            self.fail("Typedef does not produce executable python code")

    def test_07_array_type(self):
        cu_die = self._get_top_die()
        array_die = self._find_die_by_tag(cu_die, "DW_TAG_array_type")
        array_type = cast(ArrayType, Entry.get(array_die, self.elf))
        self.assertIsInstance(array_type, ArrayType, "Invalid entry type")
        self.assertIsInstance(
            array_type.associated_type, BaseType, "Invalid associated type"
        )
        self.assertEqual(
            array_type.associated_type.name, "char", "Invalid associated type"
        )
        try:
            self._exec_python_code(array_type)
        except Exception:
            self.fail("ArrayType does not produce executable python code")

    def test_08_structure_type(self):
        cu_die = self._get_top_die()
        structure_die = self._find_die_by_tag_and_name(
            cu_die, "DW_TAG_structure_type", "_assignee"
        )
        structure_type = cast(StructureType, Entry.get(structure_die, self.elf))
        self.assertIsInstance(structure_type, StructureType, "Invalid entry type")
        dependencies = structure_type.get_dependencies()
        self.assertEqual(len(dependencies), 2, "Invalid number of members")
        self.assertIsInstance(dependencies[0], BaseType, "Invalid dependency 0 type")
        self.assertEqual(dependencies[0].name, "int", "Invalid dependency 0 name")
        self.assertIsInstance(dependencies[1], ArrayType, "Invalid dependency 0 type")
        self.assertEqual(
            dependencies[1].associated_type.name, "char", "Invalid dependency 0 name"
        )
        try:
            self._exec_python_code(structure_type)
        except Exception:
            self.fail("StructureType does not produce executable python code")

    def test_09_union_type(self):
        cu_die = self._get_top_die()
        union_die = self._find_die_by_tag_and_name(
            cu_die, "DW_TAG_union_type", "_program_options_u"
        )
        union_type = cast(UnionType, Entry.get(union_die, self.elf))
        self.assertIsInstance(union_type, UnionType, "Invalid entry type")
        dependencies = union_type.get_dependencies()
        self.assertEqual(len(dependencies), 2, "Invalid number of members")
        self.assertIsInstance(
            dependencies[0], StructureType, "Invalid dependency 0 type"
        )
        self.assertEqual(dependencies[0].name, "options", "Invalid dependency 0 name")
        self.assertIsInstance(dependencies[1], Typedef, "Invalid dependency 0 type")
        self.assertEqual(dependencies[1].name, "uint8_t", "Invalid dependency 0 name")
        try:
            self._exec_python_code(union_type)
        except Exception:
            self.fail("StructureType does not produce executable python code")

    def test_10_variable(self):
        cu_die = self._get_top_die()
        variable_die = self._find_die_by_tag_and_name(cu_die, "DW_TAG_variable", "bla")
        variable_type = Variable(variable_die, self.elf)
        typ = variable_type.associated_type
        self.assertIsInstance(typ, Typedef)
        self.assertIsNone(variable_type.location, "Non static variable location known?")
        self.assertIsNone(variable_type.section, "Non static variable section known?")
        self.assertIsNone(variable_type.value, "Non static variable value known?")

        variable_die = self._find_die_by_tag_and_name(cu_die, "DW_TAG_variable", "msg")
        variable_type = Variable(variable_die, self.elf)
        typ = variable_type.associated_type
        self.assertIsInstance(typ, ArrayType)
        self.assertIsNotNone(variable_type.location, "Static variable location unknown")
        self.assertIsNotNone(variable_type.section, "Static variable section unknown")
        self.assertIsNotNone(variable_type.value, "Static variable value unknown")
        value = variable_type.value
        self.assertEqual(len(value), 6, "Dimension 0 has 6 elements")
        for i in value:
            self.assertEqual(len(i), 30, "Dimension 0 has 30 elements")
        values = ("Hello", "C++", "World", "from", "VS Code", "and the C++ extension!")
        for guess, truth in zip(value, values):
            self.assertEqual(self._char_array2str(guess), truth)
        try:
            exec(
                "\n".join(
                    (
                        self._typeable2str(variable_type.associated_type),
                        variable_type.to_python_code(),
                    )
                ),
                {},
            )
        except Exception:
            self.fail("StructureType does not produce executable python code")

    def test_11_subprogram(self):
        cu_die = self._get_top_die()
        subprogram_die = self._find_die_by_tag_and_name(
            cu_die, "DW_TAG_subprogram", "my_f"
        )
        subprogram_type = Subprogram(subprogram_die, self.elf)
        ret = subprogram_type.associated_type
        self.assertIsInstance(ret, BaseType, "Invalid return type")
        self.assertEqual(ret.name, "int", "Invalid return type name")
        args = subprogram_type.args
        self.assertEqual(len(args), 3, "Invalid number of arguments")
        self.assertIsInstance(args[0], BaseType, "Invalid arg 0 type")
        self.assertIsInstance(args[1], PointerType, "Invalid arg 1 type")
        self.assertIsInstance(args[2], StructureType, "Invalid arg 2 type")


class TestDependencyGraph(_ElfTestBase):
    def test_01_simple(self):
        cu_die = self._get_top_die()
        variable_die = self._find_die_by_tag_and_name(cu_die, "DW_TAG_variable", "uart")
        variable_type = Variable(variable_die, self.elf)
        dg = DependencyGraph((variable_type.associated_type,))
        self.assertFalse(dg.has_circular, "Circular dependency is not present")
        imports = (f"import {i}" for i in dg.get_imports())
        decls = (i.to_python_code() for i in dg.sorted)
        code = "\n".join(chain(imports, decls))
        try:
            exec(code, {})
        except Exception:
            self.fail("StructureType does not produce executable python code")

    def test_02_circular(self):
        cu_die = self._get_top_die()
        variable_die = self._find_die_by_tag_and_name(
            cu_die, "DW_TAG_variable", "my_happy"
        )
        variable_type = Variable(variable_die, self.elf)
        dg = DependencyGraph((variable_type.associated_type,))
        self.assertTrue(dg.has_circular, "Circular dependency is present")
