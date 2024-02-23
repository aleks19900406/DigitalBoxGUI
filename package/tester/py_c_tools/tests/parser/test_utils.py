import ctypes
from itertools import count
from unittest import TestCase

from c_tools.parser.utils import (
    CtypesBEStruct,
    CtypesEnum,
    CtypesLEStruct,
    CtypesStruct,
)


class TestCtypesEnum(TestCase):
    PAIRS = dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", count()))
    PAIRS_UINT8 = {"A": 0, "B": 2 ** 8 - 1}
    PAIRS_INT8 = {"A": -(2 ** 7), "B": 2 ** 7 - 1}
    PAIRS_UINT16 = {"A": 0, "B": 2 ** 16 - 1}
    PAIRS_INT16 = {"A": -(2 ** 15), "B": 2 ** 15 - 1}
    PAIRS_UINT32 = {"A": 0, "B": 2 ** 32 - 1}
    PAIRS_INT32 = {"A": -(2 ** 31), "B": 2 ** 31 - 1}
    PAIRS_UINT64 = {"A": 0, "B": 2 ** 64 - 1}
    PAIRS_INT64 = {"A": -(2 ** 63), "B": 2 ** 63 - 1}
    PAIRS_ORDER = (
        PAIRS_UINT8,
        PAIRS_INT8,
        PAIRS_UINT16,
        PAIRS_INT16,
        PAIRS_UINT32,
        PAIRS_INT32,
        PAIRS_UINT64,
        PAIRS_INT64,
    )
    SIZES_ORDER = (1, 1, 2, 2, 4, 4, 8, 8)
    INT_ORDER = (
        ctypes.c_uint8,
        ctypes.c_int8,
        ctypes.c_uint16,
        ctypes.c_int16,
        ctypes.c_uint32,
        ctypes.c_int32,
        ctypes.c_uint64,
        ctypes.c_int64,
    )
    INT_PAIRS_ORDER = dict(zip(INT_ORDER, tuple(zip(PAIRS_ORDER, SIZES_ORDER))))

    def test_01_definable(self):
        try:

            class TestEnum(CtypesEnum):
                A = None
                B = None
                C = 10
                D = None

        except Exception:
            self.fail("Enum subclass definition should not fail")

    def test_02_type_definable(self):
        Enum = type("Enum", (CtypesEnum,), self.PAIRS)

    def test_03_member_constructible(self):
        class Enum(CtypesEnum):
            A = 1

        try:
            self.assertTrue(
                Enum(1) is Enum.A, "Enum from member should return member instance"
            )
        except Exception:
            self.fail("Enum should be constructed with member")
        try:
            Enum(2)
        except Exception:
            self.fail("Enum should be constructed even with non-member value")

    def test_04_member_indexable(self):
        class Enum(CtypesEnum):
            A = 1

        try:
            self.assertTrue(
                Enum["A"] is Enum.A, "Enum from member should return member instance"
            )
        except Exception:
            self.fail("Enum should be constructed with member")

    def test_05_int_type(self):
        for typ, (pairs, size) in self.INT_PAIRS_ORDER.items():
            enum = type("enum", (CtypesEnum,), pairs)
            self.assertEqual(
                ctypes.sizeof(enum), size, f"Enum {typ.__name__} has invalid size"
            )
            self.assertEqual(
                enum._type_,
                typ._type_,
                f"Enum ({typ.__name__}) does not have a valid type",
            )

    def test_06_non_inheritable(self):
        with self.assertRaises(
            TypeError, msg="Could be impossible to inherit a CtypesEnum subclass"
        ):

            class EnumBase(CtypesEnum):
                ...

            class Enum(EnumBase):
                ...

    def test_07_ctypes_enum_subclass(self):
        class Enum(CtypesEnum):
            ...

        if not issubclass(Enum, CtypesEnum):
            self.fail("Enums must be subclasses of CtypesEnum")

    def test_08_auto_increment(self):
        class Enum(CtypesEnum):
            A = None
            B = None
            C = None
            D = 100
            E = None
            F = None
            G = 2
            H = None
            I = None

        self.assertEqual(Enum.A.value, 0, "Enum should start with 0")
        self.assertEqual(Enum.B.value, 1, "Enum auto incrementation error")
        self.assertEqual(Enum.C.value, 2, "Enum auto incrementation error")
        self.assertEqual(Enum.D.value, 100, "Enum auto incrementation error")
        self.assertEqual(Enum.E.value, 101, "Enum auto incrementation error")
        self.assertEqual(Enum.F.value, 102, "Enum auto incrementation error")
        self.assertEqual(Enum.G.value, 2, "Enum auto incrementation error")
        self.assertEqual(Enum.H.value, 3, "Enum auto incrementation error")
        self.assertEqual(Enum.I.value, 4, "Enum auto incrementation error")

    def test_09_member_isinstance(self):
        class Enum(CtypesEnum):
            A = None
            B = None
            C = 100

        class Enum1(CtypesEnum):
            A = None
            B = None
            C = 100

        for i in (Enum.A, Enum.B, Enum.C):
            self.assertIsInstance(i, Enum, f"{i} should be an instance of Enum")
            self.assertIsInstance(
                i, CtypesEnum, f"{i} should be an instance of CtypesEnum"
            )
        for i in (Enum1.A, Enum1.B, Enum1.C):
            self.assertNotIsInstance(i, Enum, f"{i} should not be an instance of Enum")

    def test_10_issubclass(self):
        class Enum(CtypesEnum):
            ...

        class Enum1(CtypesEnum):
            ...

        self.assertTrue(
            issubclass(Enum, CtypesEnum), "Enum should be a CtypesEnum subclass"
        )
        self.assertTrue(
            issubclass(Enum1, CtypesEnum), "Enum1 should be a CtypesEnum subclass"
        )
        self.assertFalse(issubclass(Enum, Enum1), "Enum should not be a Enum1 subclass")
        self.assertFalse(issubclass(Enum1, Enum), "Enum1 should not be a Enum subclass")

    def test_11_contains(self):
        class Enum(CtypesEnum):
            A = 1
            B = 2
            C = 3

        class Enum1(CtypesEnum):
            A = 1
            B = 2
            C = 3

        for i in (Enum.A, Enum.B, Enum.C):
            self.assertIn(i, Enum, f"Enum should contain {i}")
            self.assertIn(i.value, Enum, f"Enum should contain {i.value}")
            self.assertNotIn(i.value + 10, Enum, f"Enum should not contain {i.value}")
        for i in (Enum1.A, Enum1.B, Enum1.C):
            self.assertNotIn(i, Enum, f"Enum should not contain {i}")
            self.assertIn(i.value, Enum, f"Enum should contain {i.value}")

    def test_12_equals(self):
        values = {
            "A": 0x0000,
            "B": 0x0002,
            "C": 0x0064,
        }
        other = 0x0001

        class E(CtypesEnum):
            A = values["A"]
            B = values["B"]
            C = values["C"]

        for n in "ABC":
            attr = getattr(E, n)
            value = values[n]
            self.assertEqual(attr, value, "value == fail")
            self.assertEqual(attr, attr, "Enum == fail")
            self.assertNotEqual(attr, other, "other == fail")
            self.assertIs(attr, E[n], "Enum is fail")
            self.assertIsNot(attr, value, "value is fail")

    def test_13_class_getitem(self):
        Enum = type("Enum", (CtypesEnum,), self.PAIRS)
        for k, v in self.PAIRS.items():
            self.assertIs(
                Enum[k], Enum(v), "get member by name should be member by value"
            )

    def test_14_as_struct_member(self):
        Enum = type("Enum", (CtypesEnum,), self.PAIRS)

        class Struct(CtypesStruct):
            _fields_ = [("first", ctypes.c_uint8), ("second", Enum)]

        first = 1
        second = Enum.C
        s = Struct(first, second)
        self.assertEqual(s.second, Enum.C.value, "Invalid enum struct value")
        s.second = Enum.G
        self.assertEqual(s.second, Enum.G.value, "Invalid enum struct value")

    def test_15_as_packed_struct_member(self):
        Enum = type("Enum", (CtypesEnum,), self.PAIRS)

        self.assertEqual(
            Enum._type_,
            ctypes.c_uint8._type_,
            "Could not properyl compare types of different lengths",
        )

        class Struct(CtypesStruct):
            _fields_ = [
                ("first", ctypes.c_uint8, 2),
                ("second", Enum, 6),
                ("third", Enum, 7),
            ]

        first = 1
        second = Enum.F
        s = Struct(first, second, Enum.G.value)
        self.assertEqual(ctypes.sizeof(s), 2, "Invalid bitfield packing")
        self.assertEqual(Enum.F, s.second, "Invalid enum struct value")
        self.assertEqual(s.second, Enum.F, "Invalid enum struct value")
        s.second = Enum.A
        self.assertEqual(Enum.A, s.second, "Invalid enum struct value")
        self.assertEqual(s.second, Enum.A, "Invalid enum struct value")
        s.third = Enum(100)
        self.assertEqual(Enum(100), s.third, "Invalid enum struct value")
        self.assertEqual(s.third, Enum(100), "Invalid enum struct value")

    def test_16_member_names(self):
        names = ("A", "B", "SOME_NAME", "OTHER_NAME", "SOMETHING_ELSE")
        Enum = type("Enum", (CtypesEnum,), {name: n for n, name in enumerate(names)})
        for n in names:
            self.assertEqual(Enum[n].name, n, "Invalid enum name")


class TestCtypesStruct(TestCase):
    def test_01_bitfield_same_type(self):
        # Enum = type("Enum", (CtypesEnum,), {"A": -2**10, "B": 2**10})
        Enum = type("Enum", (CtypesEnum,), {"A": 0, "B": 2 ** 6 - 1})

        class Struct(CtypesStruct):
            _fields_ = [("a", ctypes.c_uint8, 2), ("b", Enum, 6)]

        self.assertEqual(ctypes.sizeof(Struct), 1, "Invalid packed struct")

    def test_02_bitfield_various_type(self):
        Enum = type("Enum", (CtypesEnum,), {"A": -(2 ** 10), "B": 2 ** 10})

        class Struct(CtypesStruct):
            _fields_ = [("a", ctypes.c_uint8, 2), ("b", Enum, 12)]

        self.assertEqual(ctypes.sizeof(Struct), 3, "Invalid packed struct")

    def test_03_bitfield_creation_assigment(self):

        for base in (CtypesStruct, CtypesLEStruct, CtypesBEStruct):
            Enum = type(
                "Enum", (CtypesEnum,), {"A": 0, "B": 0b10101010, "C": 0b01010101}
            )

            class Struct(base):
                _fields_ = [("a", ctypes.c_uint8, 2), ("b", Enum, 6)]

            try:
                s = Struct(ctypes.c_uint8(0), b=Enum.B)
            except Exception:
                self.fail("Constructing with _SimpleCData object should not fail")
            self.assertEqual(s.a, 0, "invalid Struct.a")
            self.assertEqual(s.b, Enum.B.value & 0x3F, "invalid Struct.a")
            try:
                s.b = Enum.C
            except Exception:
                self.fail("Assigning a _SimpleCData object should not fail")
            self.assertEqual(s.a, 0, "invalid Struct.a")
            self.assertEqual(s.b, Enum.C.value & 0x3F, "invalid Struct.a")

    def test_04_endianness(self):
        for e, t in (("little", CtypesLEStruct), ("big", CtypesBEStruct)):

            class S(t):
                _fields_ = [
                    ("a", ctypes.c_uint16),
                ]

            self.assertEqual(bytes(S(1)), int(1).to_bytes(2, e), f"Invalid {e} bytes")
            buff = int(1).to_bytes(2, e)
            self.assertEqual(S.from_buffer_copy(buff).a, 1, f"Invalid {e} member")

    def test_05_to_bytes(self):
        class E(CtypesEnum):
            A = 0xFFFF
            B = 0x0011

        self.assertEqual(
            ctypes.sizeof(E), ctypes.sizeof(ctypes.c_uint16), "Invalid enum size"
        )

        class S(CtypesLEStruct):
            _fields_ = [("a", ctypes.c_uint16, 5), ("b", E, 16 - 5), ("c", E)]

        s = S(ctypes.c_uint16(0xFFF1), E.A, E.B)
        self.assertEqual(s.a, 0x0011, "Invalid uint16 Struct.a")
        self.assertEqual(s.b, 0x07FF, "Invalid enum Struct.b")
        self.assertEqual(s.c, E.B.value, "Invalid enum Struct.c")
        try:
            b = bytes(s)
            bytearray(s)
        except Exception:
            self.fail("Constructing bytes out of a struct should not fail")
        self.assertEqual(b, b"\xf1\xff\x11\x00")
