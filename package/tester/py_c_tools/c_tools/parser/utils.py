"""Module introduces a set of ctypes compatible classes

:class:`CtypesStruct`, :class:`CtypesBEStruct` and :class:`CtypesLEStruct` are
subclasses of :class:`ctypes.Structure`, :class:`ctypes.BigEndianStructure` and
:class:`ctypes.LittleEndianStructure` respectively.
They come with additional option to set bit fields not only with integer values, but
also with :class:`CtypesEnum` instances.
"""
import ctypes
from dataclasses import dataclass
from types import MappingProxyType
from typing import (
    Any,
    ClassVar,
    Iterable,
    List,
    Literal,
    Mapping,
    Optional,
    Tuple,
    Type,
    Union,
)

from _ctypes import _SimpleCData

IntCtypes = Union[
    ctypes.c_uint8,
    ctypes.c_int8,
    ctypes.c_uint16,
    ctypes.c_int16,
    ctypes.c_uint32,
    ctypes.c_int32,
    ctypes.c_uint64,
    ctypes.c_int64,
]


def _int_op_translate_value(enum: "CtypesEnum", other: Any) -> int:
    if isinstance(other, type(enum)):
        return other.value
    elif isinstance(other, int):
        return other
    else:
        raise TypeError("'other' could not be translated to int")


def _int_op(enum: "CtypesEnum", op: str, other: Any) -> Any:
    return getattr(enum.value, op)(_int_op_translate_value(enum, other))


def _int_op_native_return(enum: "CtypesEnum", op: str, other: Any) -> Any:
    return type(enum)(_int_op(enum, op, other))


def _int_op_unary(enum: "CtypesEnum", op: str) -> Any:
    return getattr(enum.value, op)()


def _int_op_unary_native_return(enum: "CtypesEnum", op: str) -> Any:
    return type(enum)(_int_op_unary(enum, op))


class _CtypesEnumMeta(type(ctypes.c_int)):
    CTYPES_ORDER = (
        ctypes.c_uint8,
        ctypes.c_int8,
        ctypes.c_uint16,
        ctypes.c_int16,
        ctypes.c_uint32,
        ctypes.c_int32,
        ctypes.c_uint64,
        ctypes.c_int64,
    )

    __base: Optional[Type["CtypesEnum"]] = None
    __classes = set()

    @classmethod
    def _get_ctypes_base_type(cls, min: int, max: int) -> IntCtypes:
        for n, t in enumerate(cls.CTYPES_ORDER):
            size = ctypes.sizeof(t)
            if n % 2:
                high = 2 ** (size * 8 - 1)
                low = -high
                high -= 1
            else:
                low = 0
                high = (2 ** (size * 8)) - 1
            if min >= low and max <= high:
                return t
        raise ValueError("desired range is too wide")

    @classmethod
    def _get_members_and_dict(cls, class_dict):
        member_names = []
        member_values_map = {}
        previous = -1
        new_dict = {}
        values = set()
        for key, value in class_dict.items():
            if (
                key.startswith("_")
                or callable(value)
                or isinstance(value, (classmethod, property, staticmethod))
            ):
                new_dict[key] = value
                continue
            if value is not None:
                value = int(value)
                previous = value
            else:
                previous += 1
                value = previous
            values.add(value)
            member_names.append(key)
            member_values_map[key] = value
        if values:
            typ = cls._get_ctypes_base_type(min(values), max(values))
        else:
            typ = ctypes.c_int
        new_dict["_type_"] = typ._type_
        new_dict["__ctype_le__"] = typ.__ctype_le__
        new_dict["__ctype_be__"] = typ.__ctype_be__
        return member_names, member_values_map, new_dict

    def __new__(cls, name, bases, dct):
        if not set(cls.CTYPES_ORDER).isdisjoint(bases):
            raise TypeError("invalid type mro")
        member_names, member_values_map, class_dict = cls._get_members_and_dict(dct)
        if cls.__base is None:  # Only register CtypesEnum - don't do anything else
            cls.__base = super().__new__(cls, name, bases, class_dict)
            return cls.__base
        for base in bases:
            if base in cls.__classes:
                raise TypeError("cannot extend enumerations")
            # new_bases.append(_SimpleCData if base is cls.__base else base)
        bases = (bases[0], _SimpleCData)
        # bases = tuple(new_bases)
        obj = type(ctypes.c_int).__new__(cls, name, bases, class_dict)
        member_map = {}
        by_value = {}
        for n, v in member_values_map.items():
            instance = obj(v)
            member_map[n] = instance
            by_value[v] = instance
            setattr(instance, "_name_", n)
            setattr(obj, n, instance)
        # setattr(obj, "__init__", cls.__base.__subclass_init__)
        setattr(obj, "_member_map_", MappingProxyType(member_map))
        setattr(obj, "_member_names_", member_names)
        setattr(obj, "_member_by_value_", MappingProxyType(by_value))
        # setattr(obj, "__setattr__", cls.__base.)
        cls.__classes.add(obj)
        return obj

    def __bool__(self) -> Literal[True]:
        return True

    def __contains__(self, member):
        """Support for 'in' operator.

        Supports both int and CtypesEnum members.
        Rationale: c does not know enum class.
        """
        if not isinstance(member, (int, CtypesEnum)):
            raise TypeError(
                "unsupported operand type(s) for 'in': '{}' and '{}'".format(
                    type(member).__qualname__, self.__class__.__qualname__
                )
            )
        if isinstance(member, self):
            return member._name_ in self._member_map_
        elif isinstance(member, int):
            return member in self._member_by_value_

    def __delattr__(self, name: str) -> None:
        if name in self._member_map_:
            raise AttributeError(f"{self.__name__}: cannot delete CtypesEnum member.")

    def __setattr__(self, name: str, value: Any) -> None:
        if name in getattr(self, "_member_map_", {}):
            raise AttributeError("cannot reassign members")
        super().__setattr__(name, value)

    def __getitem__(self, name: str) -> int:
        return self._member_map_[name]

    def __len__(self) -> int:
        return len(self._member_names_)

    def __iter__(self) -> Iterable["CtypesEnum"]:
        yield from (self._member_map_[name] for name in self._member_names_)

    def __reversed__(self) -> Iterable["CtypesEnum"]:
        yield from (self._member_map_[name] for name in reversed(self._member_names_))

    def __repr__(self):
        return f"<ctypes_enum {self.__name__}>"

    @property
    def __members__(self) -> Mapping[str, "CtypesEnum"]:
        return self._member_map_


@dataclass
class Named:
    _name_: str


class CtypesEnum(metaclass=_CtypesEnumMeta):
    value: int

    def __new__(cls, value: int):
        member_map = getattr(cls, "_member_by_value_", None)
        obj = None
        if member_map:  # Class already esists, returning instances.
            obj = member_map.get(value, None)
        if obj is None:  # Object is not a valid enum or wasn't constructed yet.
            obj = super().__new__(cls)
        return obj

    def __init__(self, value: int):
        super().__init__()
        self.value = value

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}.{self.name}: {self.value}>"

    def __hash__(self) -> int:
        return hash((self.value, type(self)))

    __eq__ = lambda s, other: _int_op(s, "__eq__", other)
    __ne__ = lambda s, other: _int_op(s, "__ne__", other)
    __lt__ = lambda s, other: _int_op(s, "__lt__", other)
    __le__ = lambda s, other: _int_op(s, "__le__", other)
    __gt__ = lambda s, other: _int_op(s, "__gt__", other)
    __ge__ = lambda s, other: _int_op(s, "__ge__", other)
    __or__ = lambda s, other: _int_op_native_return(s, "__or__", other)
    __and__ = lambda s, other: _int_op_native_return(s, "__and__", other)
    __rand__ = lambda s, other: _int_op_native_return(s, "__and__", other)
    __lshift__ = lambda s, other: _int_op_native_return(s, "__lshift__", other)
    __rshift__ = lambda s, other: _int_op_native_return(s, "__rshift__", other)
    __add__ = lambda s, other: _int_op_native_return(s, "__add__", other)
    __sub__ = lambda s, other: _int_op_native_return(s, "__sub__", other)
    __xor__ = lambda s, other: _int_op_native_return(s, "__xor__", other)
    __invert__ = lambda s: _int_op_unary_native_return(s, "__invert__")

    def _derive_name(self) -> str:
        member = self._member_by_value_.get(self.value, None)
        if member is not None:
            return member._name_
        if self.value == 0:
            return "0"
        names = []
        for i in range(ctypes.sizeof(self) * 8):
            shift = 1 << i
            if shift > self.value:
                break
            if not (self.value & shift):
                continue
            member = self._member_by_value_.get(shift, Named(str(shift)))._name_
            names.insert(0, member)
        return "|".join(names)

    def _get_name(self) -> str:
        # Struct member construction could avoid new...
        name = getattr(self, "_name_", None)
        return name or self._derive_name()

    name = property(_get_name)

    @classmethod
    def from_param(cls, param):
        if isinstance(param, CtypesEnum):
            if isinstance(param, cls):
                return param
            else:
                raise TypeError("cannot mix enumeration members")
        else:
            return cls(param)


class CollectionAddon:
    _anonymous_: Tuple[str, ...]
    _fields_: List[Tuple[str, Type]]

    def __init__(self, *args, **kwargs) -> None:
        args = tuple(
            arg.value if isinstance(arg, _SimpleCData) else arg for arg in args
        )
        kwargs = {
            k: v.value if isinstance(v, _SimpleCData) else v for k, v in kwargs.items()
        }
        super().__init__(*args, **kwargs)

    def __str__(self) -> str:
        return "{\n" + "\n".join(self._member_strings()) + "\n}"

    def _member_strings(self, padding=2) -> Iterable[str]:
        for name, typ, *_ in self._fields_:
            yield self._attr2string(name, getattr(self, name), padding=padding)

    @classmethod
    def _attr2string(cls, name, attr, padding=2) -> str:
        ret = " " * padding
        if isinstance(attr, CollectionAddon):
            ret += (
                f"{name}: {{\n"
                + "\n".join(attr._member_strings(padding + 2))
                + "\n"
                + " " * padding
                + "}"
            )
        elif isinstance(attr, ctypes.Array):
            ret += f"{name}: {{\n"
            for n, item in enumerate(attr):
                ret += cls._attr2string(str(n), item, padding + 2)
                ret += "\n"
            ret += " " * padding + "}"
        else:
            ret += f"{name}: {attr}"
        return ret


class CtypesUnion(CollectionAddon, ctypes.Union):
    ...


@dataclass
class Field:
    type: Any
    bit_size: Optional[int] = None

    @property
    def is_bitfield(self):
        return self.bit_size is not None



class _LEStructMeta(type(ctypes.LittleEndianStructure)):
    def __new__(cls, name, bases, dct):
        fields = dct.get("_fields_", None)
        if fields is None:
            fields = ()
            dct["_fields_"] = fields
        dct["_field_map_"] = MappingProxyType(
            {name: Field(*param) for name, *param in fields}
        )
        return super().__new__(cls, name, bases, dct)


class _BEStructMeta(type(ctypes.BigEndianStructure)):
    def __new__(cls, name, bases, dct):
        fields = dct.get("_fields_", None)
        if fields is None:
            fields = ()
            dct["_fields_"] = fields
        dct["_field_map_"] = MappingProxyType(
            {name: Field(*param) for name, *param in fields}
        )
        return super().__new__(cls, name, bases, dct)


class StructAddon(CollectionAddon):
    """Struct adaptation to allow setting bitfields with _SimpleCData objects"""

    _pack_ = 1
    _fields_: List[Union[Tuple[str, Type], Tuple[str, Type, int]]]
    _original_fields_: List[Union[Tuple[str, Type], Tuple[str, Type, int]]]
    _field_map_: ClassVar[Mapping[str, Field]]

    def __setattr__(self, name: str, value: Any) -> None:
        field = self._field_map_.get(name, None)
        if field is not None:
            if isinstance(value, field.type):
                value = value.value
            elif isinstance(value, int):
                pass
            else:
                raise TypeError(
                    f"incompatible types, {type(value).__name__} instance instead of "
                    + f"{field.type.__name__} instance"
                )
        super().__setattr__(name, value)


class CtypesBEStruct(StructAddon, ctypes.BigEndianStructure, metaclass=_BEStructMeta):
    ...


class CtypesLEStruct(StructAddon, ctypes.LittleEndianStructure, metaclass=_LEStructMeta):
    ...


if ctypes.Structure == ctypes.LittleEndianStructure:
    CtypesStruct = CtypesLEStruct
else:
    CtypesStruct = CtypesBEStruct
