import ctypes
import pathlib
import re
from abc import ABC, ABCMeta, abstractmethod
from dataclasses import dataclass, field
from functools import cached_property, reduce
from typing import (
    Any,
    Callable,
    ClassVar,
    DefaultDict,
    Dict,
    Generic,
    Iterable,
    List,
    Literal,
    Optional,
    Protocol,
    Sequence,
    Set,
    SupportsBytes,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

import black as _black
import isort as _isort
from elftools.dwarf import constants as _const
from elftools.dwarf.die import DIE as _DIE
from elftools.dwarf.die import AttributeValue as _AttributeValue
from elftools.elf import sections as _sections
from elftools.elf.elffile import ELFFile as _ELFFile
from lxml import etree
from lxml.etree import Element, _Element

from c_tools.parser import utils as _utils

CtypeTypes = Type[
    Union[
        ctypes.BigEndianStructure,
        ctypes.LittleEndianStructure,
        ctypes.Structure,
        ctypes._SimpleCData,
        ctypes.Array,
    ]
]

ST = TypeVar("ST", bound=_sections.Section)  #: Section type


class Section:
    """ELF section description

    :param section: belonging section object
    """

    def __init__(self, section: _sections.Section) -> None:
        self._section = section
        self.name = section.name
        self.start = section.header.sh_addr
        self.end = self.start + section.header.sh_size
        self.data = section.data

    def __contains__(self, entity_address: Union["Entity", int]) -> bool:
        """Support for `in` operator.

        :param entity: entity to check

        Checks whether an entity data resides in a section.
        """
        if isinstance(entity_address, Entity):
            location = entity_address.location if entity_address.location else -1
        else:
            location = entity_address
        if location is not None:
            return self.start <= location < self.end
        else:
            return False

    def __iter__(self) -> Iterable[_sections.Symbol]:
        """`iteration` support"""
        if not isinstance(self._section, _sections.SymbolTableSection):
            return
        yield from self._section.iter_symbols()


class Sections(Iterable):
    """ELF section explorer

    :param elf: ELF file containing sections
    """

    def __init__(self, elf: _ELFFile) -> None:
        self._elf = elf

    def __iter__(self) -> Iterable[Section]:
        """`iteration` support"""
        yield from map(lambda i: Section(i), self._elf.iter_sections())

    def section_by_entity(self, entity: "Entity") -> Optional[Section]:
        """Returns a section that the entity data resides in

        :param entity: Entity object to search by
        :return: Section, containing the address of the given Entity
        """
        for section in self._elf.iter_sections():
            s = Section(section)
            if entity in s:
                return s
        return None

    def section_by_address(self, address: int) -> Optional[Section]:
        """Returns a section that spans over the given address

        :param address: address to get the section by
        :return: section that spans over the giver address, or None if not found
        """
        for section in self._elf.iter_sections():
            s = Section(section)
            if address in s:
                return s
        return None

    def iter_sections_by_type(self, section_type: Type[ST]) -> Iterable[ST]:
        """Iters through sections of given type

        :param section_type: section type to iter by
        :type section_type: Type[ST]
        :yield: Section of given section type
        """
        yield from filter(
            lambda i: isinstance(i, section_type), self._elf.iter_sections()
        )


def die2hash(die: _DIE) -> int:
    """Derives hash from die. Used to fetch the unique hash for two DIE instances of the
    same DWARF object

    :param die: DIE object
    :return: unique hash per each DWARF object
    """
    return hash((die.cu.header.debug_abbrev_offset, die.offset))


def get_linked_die_by_attr(die: _DIE, attr: str) -> _DIE:
    """Get linked DIE by value of linking attribute

    :param die: DIE object
    :param attr: attribute to get the linked object by
    :return: linked DIE object

    Known linking attributes:
    * DW_AT_type
    * DW_AT_specifications
    """
    attrs = die.attributes
    try:
        offset = attrs[attr].value + die.cu.cu_offset
        return _DIE(die.cu, die.cu.dwarfinfo.debug_info_sec.stream, offset)
    except Exception as e:
        raise type(e)(
            "DIE:\n"
            + str(die)
            + "\n"
            + "\n".join(f"{k}: {v}" for k, v in attrs)
            + "\nfailed with exception message: "
            + str(e)
        ) from None


def get_linked_die(die: _DIE) -> _DIE:
    """Get linked DIE by value of DW_AT_type

    :param die: DIE object
    :return: linked DIE object
    """
    return get_linked_die_by_attr(die, "DW_AT_type")


def get_linked_type(die: _DIE, elf: _ELFFile) -> "Typeable":
    """Get linked Typeable of a DIE

    :param die: DIE object
    :return: linked Typeable object
    """
    die = get_linked_die(die)
    if die is None:
        raise ValueError("DIE has no linked DIE")
    typ = Entry.get(die, elf)
    if not isinstance(typ, Typeable):
        raise TypeError(f"linked object ({typ}) is not Typeable")
    return typ


def die_name2class_name(name: Union[str, bytes]) -> str:
    """Derives class name from DIE name

    :param name: name of the _DIE entry
    :return: derived class name
    """
    if isinstance(name, bytes):
        name = name.decode()
    return ("_" if name.startswith("_") else "") + "".join(
        i.capitalize() for i in re.split(" |_", name) if i
    )


class EntryMeta(ABCMeta):
    """Meta class used for Entry and its derivatives.

    Meta class provides storage of Entry instances.
    When a new Entry is about to be created from a DIE, the Entry class looks for
    existing instance, mapped to the same DIE.
    Each Entry derivate - if representing an implementation of a certain DIE tag -
    should provide a list a set of supported DIE tags it implements.
    Tag re-implementation is prohibited.
    """

    _type_lookup: Dict[
        Optional[str], Union[Callable[[_DIE, _ELFFile], "Entry"], Type["Entry"]]
    ] = {
        "DW_TAG_volatile_type": get_linked_type,
        "DW_TAG_const_type": get_linked_type,
    }
    _entries = DefaultDict[_ELFFile, DefaultDict[Optional[str], Dict[int, "Entry"]]](
        lambda: DefaultDict(dict)
    )
    SUPPORTED_TAGS: Set[str]

    def __new__(cls, name: str, bases: Tuple[type], dct: Dict[str, Any]):
        obj = cast(Type["Entry"], super().__new__(cls, name, bases, dct))
        for supported_tag in obj.SUPPORTED_TAGS:
            typ = cls._type_lookup.get(supported_tag)
            if typ is not None:
                raise TypeError(
                    f"type, supporting {supported_tag} already registered ({typ})"
                )
            cls._type_lookup[supported_tag] = obj
        return obj

    def get(self, die: _DIE, elf: _ELFFile) -> "Entry":
        """Support for Entry generation by DIEs.

        If an instance of Entry, bound to the DIE already exists, it is returned,
        else it is created and registered to a collection of Entries.

        :param die: DIE to get a Entry by
        :param elf: ELF file the entity resides in
        :raises TypeError: in case no Entry subclass implements the given DIE tag
        :return: Entry instance, bound to the given DIE
        """
        tag = cast(Optional[str], die.tag)
        by_tag = self._entries[elf][tag]
        h = die2hash(die)
        if (entry := by_tag.get(h)) is not None:
            return entry
        try:
            typ = self._type_lookup[tag]
        except KeyError:
            print(die)
            raise TypeError(f"{tag} is not supported tag") from None
        return typ(die, elf)


class Entry(object, metaclass=EntryMeta):
    """Base class for following DIE tag implementations

    :param die: DIE for the new Entry to be constructed from and bound to
    :param elf: ELF file, the DIE resides in

    .. note::

        DIE instance of the same DWARF object does not share the same hash.
        In order to bind a Entry to the DIE, the :func:`die2hash` function is used.
    """

    die: _DIE  #: bound DIE
    elf: _ELFFile
    name: Optional[str] = None  #: Entry name if DIE it has one, else None

    SUPPORTED_TAGS: ClassVar[Set[str]] = set()  #: A set of supported DIE tags

    def __new__(cls, die: _DIE, elf: _ELFFile):
        # Prevent instance duplication
        entries = cls._entries[elf][die.tag]
        h = die2hash(die)
        obj = entries.get(h)
        if obj is None:
            cls._validate_die(die)
            obj = super().__new__(cls)
            entries[h] = obj
        return obj

    def __init__(self, die: _DIE, elf: _ELFFile) -> None:
        self.die = die
        self.elf = elf
        self.name = self._derive_name()
        self._after_entry_init_()

    def _after_entry_init_(self):
        """Meant to be accessed right after the `die`, `elf` and `name` are set"""
        pass

    def _derive_name(self) -> Optional[str]:
        """Derives a name from a DIE"""
        attrs = self.die.attributes
        return None if "DW_AT_name" not in attrs else attrs["DW_AT_name"].value.decode()

    def _get_attribute(self, name: str) -> Optional[_AttributeValue]:
        return self.die.attributes.get(name, None)

    @classmethod
    def _validate_die(cls, die) -> None:
        """Validates whether a class supports the DIE of the given tag"""
        if die.tag not in cls.SUPPORTED_TAGS:
            raise ValueError(f"{cls.__name__} does not support {die.tag}")


BASE = TypeVar(
    "BASE",
    bound=Union[ctypes.Union, ctypes._SimpleCData, ctypes.Structure, _utils.CtypesEnum],
)

INTEGRAL_BASE = TypeVar(
    "INTEGRAL_BASE", bound=Union[ctypes._SimpleCData, _utils.CtypesEnum]
)


class Typeable(Entry, Generic[BASE]):
    """Base class for all DIEs that represents a type or are linked to it"""

    base: Type[BASE]
    """ctypes base class to be used by :meth:`Typeable.to_ctype`"""
    base_name: str
    """ctypes base class name to be used by :meth:`Typeable.to_python_code`"""
    class_name: str  #: ctypes class name to be used by :meth:`Typeable.to_python_code`
    users: List["Typeable"]  #: A list of types, using this type

    def __init__(self, die: _DIE, elf: _ELFFile) -> None:
        super().__init__(die, elf)
        self.class_name = self._derive_class_name()
        self.users = []
        self._ctype: Optional[Type[BASE]] = None

    def __str__(self) -> str:
        return self.to_python_code()

    def _get_filename(self) -> Optional[str]:
        file = self._get_attribute("DW_AT_decl_file")
        if not file:
            return None
        file_idx = file.value
        cu = self.die.cu
        top_die = cu.get_top_DIE()
        dwarf = cu.dwarfinfo
        lp = dwarf.line_program_for_CU(cu)
        file_entry = lp.header.file_entry[file_idx - 1]
        filename = file_entry.name
        dir_index = file_entry.dir_index
        if dir_index:
            directory = lp.header.include_directory[dir_index - 1]
        else:
            directory = top_die.attributes["DW_AT_comp_dir"].value
        return pathlib.Path(directory.decode()) / filename.decode()

    @cached_property
    def decl(self) -> str:
        file = self._get_filename()
        line = self.die.attributes.get("DW_AT_decl_line", None)
        column = self.die.attributes.get("DW_AT_decl_column", None)
        if file and line and column:
            ret = f"{file}:{line.value},{column.value}"
        else:
            ret = "declaration unknown"
        return ret

    def _derive_class_name(self) -> str:
        """Derives python class name

        .. note::

            This method should only be called once per instance.

        .. seealso::

            :class:`NoNameTypeable` prevents multiple method execution per instance due
            to unnamed type enumeration.
        """
        return die_name2class_name(cast(str, self.name))

    @abstractmethod
    def _derive_ctype(self) -> Type[BASE]:
        """Derivation of ctypes class

        :return: derived ctype
        """
        raise NotImplementedError("method not implemented")

    def to_ctype(self) -> Type[BASE]:
        """DIE to ctypes type

        :return: ctype representation of a DIE entry
        """
        if self._ctype is None:
            self._ctype = self._derive_ctype()
        return self._ctype

    @abstractmethod
    def to_python_code(self) -> str:
        """DIE to python code

        :return: python code representation of a DIE entry
        """
        raise NotImplementedError("method not implemented")

    @abstractmethod
    def get_python_imports(self) -> Tuple[str, ...]:
        """A sequence of imports, needed by python code string

        :return: tuple of depending modules
        """
        raise NotImplementedError("method not implemented")

    @abstractmethod
    def var_python_code(
        self,
        var_name: str,
        value: "ExportableVariable",
        subtype_name: Optional[str] = None,
    ) -> str:
        """Types instance python string representation

        :param var_name: target variable name
        :param value: value, needed by type to instantiate
        :param subtype_name: in case of typedef, the optional name of a type
        :return: instance python string representation
        """
        raise NotImplementedError("method is not implemented")


class NoNameTypeable(Typeable[BASE]):
    """Base class for types which could be unnamed"""

    CLASS_NAME: ClassVar[str]  #: Class name prefix

    _no_name_cnt: ClassVar[int] = 0
    _cnt: int
    _unnamed: bool = True

    def _derive_class_name(self) -> str:
        """Derives python class name

        .. note::

            This method could only be called once per instance to register it's own
            counter value.
        """
        name = self.name
        if name is None:
            self._cnt = self._no_name_cnt
            NoNameTypeable._no_name_cnt += 1
            return self._get_unnamed_class_name()
        self._unnamed = False
        return die_name2class_name(name)

    def _get_unnamed_class_name(self) -> str:
        if (parent := self.die.get_parent()) is not None:
            parent_name = parent.attributes["DW_AT_name"].value.decode()
            if parent.tag == "DW_TAG_compile_unit":
                parent_name = pathlib.Path(parent_name).stem
            return f"_{die_name2class_name(parent_name)}_member{self._cnt}"
        name = "_Unnamed{}{}".format(die_name2class_name(self.CLASS_NAME), self._cnt)
        return name

    def update_class_name(self) -> None:
        """Updates class name in case it is unnamed

        Method should be called in case the class user has been added.
        """
        if self._unnamed:
            if not self.users:
                pass
            if len(self.users) == 1:
                self.class_name = f"{self.users[0].class_name}Member_{self._cnt}"
                if not self.class_name.startswith("_"):
                    self.class_name = "_" + self.class_name
            else:
                self.class_name = self._get_unnamed_class_name()
                self._unnamed = False


ASSOCIATION = TypeVar("ASSOCIATION", bound=Optional[Typeable])


class DependentType(Typeable[BASE], Generic[BASE, ASSOCIATION]):
    """Base class for Dependent types"""

    @abstractmethod
    def get_dependencies(self) -> Tuple[ASSOCIATION, ...]:
        """A sequence of types the python representation of DIE depends on

        :return: tuple of depending Typeable objects
        """
        ...


class AssociatedType(DependentType[BASE, ASSOCIATION]):
    """Base class for Associated types"""

    def __init__(self, die: _DIE, elf: _ELFFile) -> None:
        super().__init__(die, elf)
        self.associated_type = self._derive_associated_type()
        if self.associated_type is not None:
            self.associated_type.users.append(self)

    @abstractmethod
    def _derive_associated_type(self) -> ASSOCIATION:
        """Derives an associated type

        :return: associated type
        """
        ...

    def get_dependencies(self) -> Tuple[ASSOCIATION, ...]:
        return (self.associated_type,) if self.associated_type else ()


class IntegralType(Typeable[INTEGRAL_BASE]):
    """Base class for Integral types"""

    base: Type[INTEGRAL_BASE]

    # TODO: Integral types will fail due to lack of __ctype_be__ and __ctype_le__ attrs.
    type: str  #: Ctypes string representation of integral type

    _INTEGRAL_TYPES = {
        _const.DW_ATE_float: {4: ctypes.c_float, 8: ctypes.c_double},
        _const.DW_ATE_unsigned_char: {
            1: ctypes.c_uint8,
        },
        _const.DW_ATE_signed_char: {
            1: ctypes.c_int8,
        },
        _const.DW_ATE_unsigned: {
            1: ctypes.c_uint8,
            2: ctypes.c_uint16,
            4: ctypes.c_uint32,
            8: ctypes.c_uint64,
        },
        _const.DW_ATE_signed: {
            1: ctypes.c_int8,
            2: ctypes.c_int16,
            4: ctypes.c_int32,
            8: ctypes.c_int64,
        },
        _const.DW_ATE_boolean: {
            1: ctypes.c_bool,
        },
        _const.DW_ATE_address: {
            4: ctypes.c_uint32,
            8: ctypes.c_uint64,
        },
    }

    def _after_entry_init_(self) -> None:
        self.type = self._derive_integral_type()

    @abstractmethod
    def _derive_integral_type(self) -> str:
        """Derive a ctypes string representation of integral type

        :return: string representation of integral type
        """
        raise NotImplementedError("not implemented")

    def _derive_ctype(self):
        return type(
            self.class_name,
            (self.base,),
            {"_type_": self.type},
        )

    def to_python_code(self) -> str:
        if self.class_name is None:  # Integral type without a name?
            raise ValueError("Unknown name of integral type - what just happened?")
        name = self.class_name
        content = f'_type_ = "{self.type}"'
        class_str = "class {name}({base}):{content}".format(
            name=name, base=self.base_name, content=f"\n    {content}"
        )
        return _black.format_str(class_str, mode=_black.Mode())

    def get_python_imports(self) -> Tuple[str, ...]:
        return ("ctypes",)

    @classmethod
    def _get_integral_type(cls, size: int, encoding: int) -> str:
        """Returns a ctype integral string by size and encoding

        :param size: byte size of an integral type
        :param encoding: DWARF encoding of an integral type
        :return: ctypes integral string
        """
        return cls._INTEGRAL_TYPES[encoding][size]._type_

    def var_python_code(
        self,
        var_name: str,
        value: "ExportableVariable",
        subtype_name: Optional[str] = None,
    ) -> str:
        return f"{var_name} = {subtype_name or self.class_name}({value})"


class BaseType(IntegralType[ctypes._SimpleCData]):
    """Supports `DW_TAG_base_type` entries parsing"""

    base = ctypes._SimpleCData
    base_name = "ctypes._SimpleCData"

    SUPPORTED_TAGS = {"DW_TAG_base_type"}

    def _derive_integral_type(self) -> str:
        attrs = self.die.attributes
        size = attrs["DW_AT_byte_size"].value
        encoding = attrs["DW_AT_encoding"].value
        return self._get_integral_type(size, encoding)


class PointerType(IntegralType[ctypes._SimpleCData], AssociatedType):
    """Supports `DW_TAG_pointer_type` entries parsing"""

    base = ctypes._SimpleCData
    base_name = "ctypes._SimpleCData"

    SUPPORTED_TAGS = {"DW_TAG_pointer_type"}

    def _derive_class_name(self) -> str:
        return "Pointer"

    def _derive_associated_type(self) -> Optional[Typeable]:
        if "DW_AT_type" not in self.die.attributes:  # void pointer
            return None
        return get_linked_type(self.die, self.elf)

    def _derive_integral_type(self) -> str:
        size = self.die.cu.header.address_size
        return self._get_integral_type(size, _const.DW_ATE_address)


class EnumerationType(IntegralType[_utils.CtypesEnum], NoNameTypeable):
    """Supports `DW_TAG_enumeration_type` entries parsing"""

    SUPPORTED_TAGS = {"DW_TAG_enumeration_type"}
    CLASS_NAME = "Enum"

    base = _utils.CtypesEnum
    base_name = f"{base.__module__}.{base.__name__}"

    def _derive_integral_type(self) -> str:
        attrs = self.die.attributes
        if "DW_AT_type" in attrs:
            # TODO: Always a base type?
            base_type: BaseType = cast(BaseType, get_linked_type(self.die, self.elf))
            return base_type.type
        else:
            return super()._derive_integral_type()

    def _derive_enumerators(self) -> Dict[str, int]:
        return {
            child.attributes["DW_AT_name"]
            .value.decode(): child.attributes["DW_AT_const_value"]
            .value
            for child in self.die.iter_children()
            if child.tag == "DW_TAG_enumerator"
        }

    def _derive_ctype(self) -> Type[_utils.CtypesEnum]:
        dct = cast(Dict[str, Any], self._derive_enumerators())
        dct["_type_"] = self.type
        return cast(Type[_utils.CtypesEnum], type(self.class_name, (self.base,), dct))

    def to_python_code(self) -> str:
        content = (
            f'_type_ = "{self.type}"',
            *(
                f"{name} = {value}"
                for name, value in self._derive_enumerators().items()
            ),
        )
        code = "class {name}({base}):\n    {content}".format(
            name=self.class_name, base=self.base_name, content="\n    ".join(content)
        )
        return _black.format_str(code, mode=_black.Mode())

    def get_python_imports(self) -> Tuple[str]:
        return ("c_tools.parser.utils",)

    def get_dependencies(self) -> Tuple[Typeable, ...]:
        return ()


class Typedef(AssociatedType[BASE, Typeable]):
    """Supports `DW_TAG_typedef` entries parsing"""

    SUPPORTED_TAGS = {"DW_TAG_typedef"}

    def _derive_associated_type(self) -> Typeable:
        return get_linked_type(self.die, self.elf)

    def _derive_ctype(self) -> Type[BASE]:
        if self.associated_type is None:
            raise ValueError("typedef needs an associated type do relate to")
        return self.associated_type.to_ctype()

    def to_python_code(self) -> str:
        return _black.format_str(
            "{} = {}".format(self.class_name, self.associated_type.class_name),
            mode=_black.Mode(),
        )

    def get_python_imports(self) -> Tuple[str, ...]:
        return ()

    def var_python_code(
        self,
        var_name: str,
        value: "ExportableVariable",
        subtype_name: Optional[str] = None,
    ) -> str:
        return self.associated_type.var_python_code(
            var_name, value, subtype_name or self.class_name
        )


class ArrayType(AssociatedType, NoNameTypeable):
    # TODO: Does not handle multidimensional arrays
    """Supports `DW_TAG_array_type` entries parsing"""
    SUPPORTED_TAGS = {"DW_TAG_array_type"}

    CLASS_NAME = "Array"

    def __init__(self, die: _DIE, elf: _ELFFile) -> None:
        super().__init__(die, elf)
        self.shape = self._derive_shape()

    def _derive_associated_type(self):
        return get_linked_type(self.die, self.elf)

    def _derive_shape(self) -> Tuple[int, ...]:
        shape: List[int] = []
        for child in self.die.iter_children():
            if not (child.tag == "DW_TAG_subrange_type"):
                raise ValueError("Array child DIE is not a subrange type")
            if "DW_AT_upper_bound" not in child.attributes:
                shape.append(0)
            else:
                shape.append(child.attributes["DW_AT_upper_bound"].value + 1)
        return tuple(reversed(shape))

    def _derive_ctype(self) -> Type[ctypes.Array]:
        return cast(
            Type[ctypes.Array],
            reduce(lambda x, y: x * y, self.shape, self.associated_type.to_ctype()),
        )

    def to_python_code(self) -> str:
        assign = reduce(
            lambda x, y: f"({x}) * {y}", self.shape, self.associated_type.class_name
        )
        code = "{name} = {assign}".format(name=self.class_name, assign=assign)
        return _black.format_str(code, mode=_black.Mode())

    def get_python_imports(self) -> Tuple[str, ...]:
        return ()

    def var_python_code(
        self,
        var_name: str,
        value: "ExportableVariable",
        subtype_name: Optional[str] = None,
    ) -> str:
        return (
            f"{var_name} = "
            f"{subtype_name or self.class_name}.from_buffer_copy({bytes(value.value)})"
        )


class MemberTypeProto(Protocol[BASE]):
    name: Optional[str]
    class_name: str
    users: List[Typeable]

    def to_ctype(self) -> Type[BASE]:
        ...

    def to_python_code(self) -> str:
        ...

    def get_python_imports(self) -> Tuple[str, ...]:
        ...

    def var_python_code(
        self,
        var_name: str,
        value: "ExportableVariable",
        subtype_name: Optional[str] = None,
    ) -> str:
        ...


class IntegralPaddingType(MemberTypeProto[ctypes.c_uint8]):
    __instances__: Dict[int, "IntegralPaddingType"] = {}

    def __new__(cls, size: int):
        ret = cls.__instances__.get(size, None)
        if ret is None:
            ret = super().__new__(cls)
            cls.__instances__[size] = ret
        return ret

    def __init__(self, size: int) -> None:
        self._size = size
        self.name = None
        self.class_name = f"IntegralPaddingType{self._size}"
        self.users = []

    def to_ctype(self) -> Type[ctypes.c_uint8]:
        return ctypes.c_uint8

    def to_python_code(self) -> str:
        return f"{self.class_name} = ctypes.c_uint8"

    def get_python_imports(self) -> Tuple[str, ...]:
        return ("ctypes",)

    def var_python_code(
        self,
        var_name: str,
        value: "ExportableVariable",
        subtype_name: Optional[str] = None,
    ) -> str:
        raise RuntimeError("Padding buffer variable could not be directly constructed")


class ArrayPaddingType(MemberTypeProto[ctypes.Array]):
    __instances__: Dict[int, "ArrayPaddingType"] = {}

    def __new__(cls, size: int):
        ret = cls.__instances__.get(size, None)
        if ret is None:
            ret = super().__new__(cls)
            cls.__instances__[size] = ret
        return ret

    def __init__(self, size: int) -> None:
        self._size = size
        self.shape = (size,)
        self.name = None
        self.class_name = f"ArrayPaddingType{self._size}"
        self.users = []

    def to_ctype(self) -> Type[ctypes.Array]:
        return ctypes.c_uint8 * self._size

    def to_python_code(self) -> str:
        return f"{self.class_name} = ctypes.c_uint8 * {self._size}"

    def get_python_imports(self) -> Tuple[str, ...]:
        return ("ctypes",)

    def var_python_code(
        self,
        var_name: str,
        value: "ExportableVariable",
        subtype_name: Optional[str] = None,
    ) -> str:
        raise RuntimeError("Padding buffer variable could not be directly constructed")


@dataclass
class Member(Generic[BASE]):
    """Member object of for :class:`ContainerTypeable`"""

    name: str
    type: MemberTypeProto[BASE]
    bit_length: Optional[int] = None
    size: int = field(init=False)

    def __post_init__(self):
        self.size = self.bit_length or ctypes.sizeof(self.type.to_ctype()) * 8

    def __str__(self):
        return (
            f'("{self.name}", {self.type.class_name})'
            if self.bit_length is None
            else f'("{self.name}", {self.type.class_name}, {self.bit_length})'
        )

    def as_tuple(
        self,
    ) -> Union[Tuple[str, Type[BASE]], Tuple[str, Type[BASE], int]]:
        """Tuple representation of a member

        :return: member as tuple
        """
        if self.bit_length is None:
            return (self.name, self.type.to_ctype())
        else:
            return (self.name, self.type.to_ctype(), self.bit_length)


class ContainerTypeable(DependentType[BASE, ASSOCIATION], NoNameTypeable):
    """Base class for union and struct"""

    def __init__(self, die: _DIE, elf: _ELFFile) -> None:
        super().__init__(die, elf)
        self._no_name_member_cnt = 0
        self.anonymous: List[str] = []
        self.members = self._derive_members()

    def _iter_members(self) -> Iterable[_DIE]:
        yield from filter(lambda i: i.tag == "DW_TAG_member", self.die.iter_children())

    @abstractmethod
    def _derive_members(self) -> List[Member]:
        ...

    def _get_anonymous_str(self) -> str:
        return "({}{})".format(
            ", ".join(f"\"{anon}\"" for anon in self.anonymous),
            "," if len(self.anonymous) == 1 else "",
        )

    def _get_ctype_members(
        self,
    ) -> List[Union[Tuple[str, Type[BASE]], Tuple[str, Type[BASE], int]]]:
        return [member.as_tuple() for member in self.members]

    def _get_members_str(self) -> str:
        return "[{}]".format(", ".join(str(member) for member in self.members))

    def get_dependencies(self) -> Tuple[ASSOCIATION, ...]:
        return tuple(member.type for member in self.members)


class StructureType(ContainerTypeable):
    """Supports `DW_TAG_structure_type` entries parsing"""

    SUPPORTED_TAGS = {"DW_TAG_structure_type"}
    CLASS_NAME = "Struct"

    def __init__(self, die: _DIE, elf: _ELFFile) -> None:
        self.base = (
            _utils.CtypesLEStruct
            if die.cu.structs.little_endian
            else _utils.CtypesBEStruct
        )
        self.base_name = (
            "c_tools.parser.utils.CtypesLEStruct"
            if die.cu.structs.little_endian
            else "c_tools.parser.utils.CtypesBEStruct"
        )
        super().__init__(die, elf)

    def _derive_members(
        self,
    ) -> List[Member]:
        members: Dict[int, Member] = {}
        no_name_member_cnt = 0
        for member in self._iter_members():
            attrs = member.attributes
            if "DW_AT_name" in attrs:
                name = attrs["DW_AT_name"].value.decode()
            else:
                name = "__anonymous{}".format(no_name_member_cnt)
                self.anonymous.append(name)
                no_name_member_cnt += 1
            typ = get_linked_type(member, self.elf)
            if isinstance(typ, Typeable):
                typ.users.append(self)
                if isinstance(typ, NoNameTypeable):
                    typ.update_class_name()
            if typ is None:
                raise RuntimeError(f"member type ({typ.die.tag}) not supported")
            bit_size = attrs.get("DW_AT_bit_size", None)
            location = attrs.get("DW_AT_data_member_location", None)
            location = 0 if location is None else location.value
            if "DW_AT_bit_size" in attrs:
                bit_size = attrs["DW_AT_bit_size"].value
                {1, 2, 3}.issubset({2})
                if (
                    "DW_AT_bit_offset" in attrs
                    and "DW_AT_data_member_location" in attrs
                ):
                    location = (
                        attrs["DW_AT_byte_size"].value
                        + attrs["DW_AT_data_member_location"].value
                    ) * 8 - (attrs["DW_AT_bit_offset"].value + bit_size)
                else:
                    raise RuntimeError(
                        "Bit size requires bit offset and data member location"
                    )
                members[location] = Member(name, typ, bit_size)
            else:
                if "DW_AT_bit_offset" in attrs:
                    raise RuntimeError("Bit offset in non bitfield?")
                elif "DW_AT_data_member_location" in attrs:
                    location = attrs["DW_AT_data_member_location"].value * 8
                else:
                    location = 0
                members[location] = Member(name, typ)
        complete_members = []
        size = 0  # in bits
        paddings = 0
        for location in sorted(members):
            diff = location - size
            if diff > 0:
                if diff < 8:
                    padding = Member(
                        f"__PADDING{paddings}", IntegralPaddingType(diff), diff
                    )
                    complete_members.append(padding)
                else:
                    padding = Member(
                        f"__PADDING{paddings}", ArrayPaddingType(diff // 8)
                    )
                    complete_members.append(padding)
                paddings += 1
                size += diff
            member = members[location]
            complete_members.append(member)
            size += member.size
        return complete_members

    def _get_ctype_members(
        self,
    ) -> List[Union[Tuple[str, Type[BASE]], Tuple[str, Type[BASE], int]]]:
        return [member.as_tuple() for member in self.members]

    def _derive_ctype(self) -> Type[ctypes.Structure]:
        dct = {
            "_pack_": True,
            "_anonymous_": tuple(self.anonymous),
            "_fields_": self._get_ctype_members(),
        }
        return cast(Type[ctypes.Structure], type(self.class_name, (self.base,), dct))

    def to_python_code(self) -> str:
        content = (
            "_pack_ = True",
            "_anonymous_ = {}".format(self._get_anonymous_str()),
            "_fields_ = {}".format(self._get_members_str()),
        )
        code = "class {name}({base}):\n    {content}".format(
            name=self.class_name, base=self.base_name, content="\n    ".join(content)
        )
        return _black.format_str(code, mode=_black.Mode())

    def get_python_imports(self) -> Tuple[str, ...]:
        return ("c_tools.parser.utils",)

    def var_python_code(
        self,
        var_name: str,
        value: "ExportableVariable",
        subtype_name: Optional[str] = None,
    ) -> str:
        return (
            f"{var_name} = "
            f"{subtype_name or self.class_name}."
            f"from_buffer_copy({bytes(value.value)!s})"
        )


class UnionType(ContainerTypeable):
    """Supports `DW_TAG_union_type` entries parsing"""

    SUPPORTED_TAGS = {"DW_TAG_union_type"}
    CLASS_NAME = "Union"
    base: ClassVar[Type[ctypes.Union]] = _utils.CtypesUnion
    base_name = "c_tools.parser.utils.CtypesUnion"

    def _derive_members(
        self,
    ) -> List[Member]:
        members: List[Member] = []
        no_name_member_cnt = 0
        for member in self._iter_members():
            attrs = member.attributes
            if "DW_AT_name" in attrs:
                name = attrs["DW_AT_name"].value.decode()
            else:
                name = "__anonymous{}".format(no_name_member_cnt)
                self.anonymous.append(name)
                no_name_member_cnt += 1
            typ = get_linked_type(member, self.elf)
            if isinstance(typ, Typeable):
                typ.users.append(self)
                if isinstance(typ, NoNameTypeable):
                    typ.update_class_name()
            if typ is None:
                raise RuntimeError(f"member type ({typ.die.tag}) not supported")
            if "DW_AT_bit_size" in attrs:
                raise RuntimeError(f"Why using a bitfield in a union? ({self.decl})")
            members.append(Member(name, typ))
        return members

    def _derive_ctype(self) -> Type[ctypes.Union]:
        dct = {
            "_anonymous_": tuple(self.anonymous),
            "_fields_": self._get_ctype_members(),
        }
        return cast(Type[ctypes.Union], type(self.class_name, (self.base,), dct))

    def to_python_code(self) -> str:
        content = (
            "_anonymous_ = {}".format(self._get_anonymous_str()),
            "_fields_ = {}".format(self._get_members_str()),
        )
        code = "class {name}({base}):\n    {content}".format(
            name=self.class_name, base=self.base_name, content="\n    ".join(content)
        )
        return _black.format_str(code, mode=_black.Mode())

    def get_python_imports(self) -> Tuple[str, ...]:
        return ("c_tools.parser.utils",)

    def var_python_code(
        self,
        var_name: str,
        value: "ExportableVariable",
        subtype_name: Optional[str] = None,
    ) -> str:
        return (
            f"{var_name} = "
            f"{subtype_name or self.class_name}."
            f"from_buffer_copy({bytes(value.value)!s})"
        )


class Subroutine(NoNameTypeable):
    # TODO: Not implemented at all
    SUPPORTED_TAGS = {"DW_TAG_subroutine_type"}

    CLASS_NAME = "Subroutine"

    def _derive_ctype(self) -> Type[CtypeTypes]:
        raise NotImplementedError("not implemented as never seemed to be used")

    def get_dependencies(self) -> Tuple["Typeable", ...]:
        return ()

    def to_python_code(self) -> str:
        return ""

    def get_python_imports(self) -> Tuple[str, ...]:
        return ()

    def var_python_code(
        self,
        var_name: str,
        value: "ExportableVariable",
        subtype_name: Optional[str] = None,
    ) -> str:
        # Not implemented error
        return super().var_python_code(var_name, value, subtype_name=subtype_name)


class Entity(Entry):
    """Base class for DIEs that consist of data"""

    location: Optional[int] = None
    value: Optional[SupportsBytes]

    def __init__(self, die: _DIE, elf: _ELFFile) -> None:
        super().__init__(die, elf)
        self.associated_type = self._derive_associated_type()
        self.location = self._derive_location()
        self.section = Sections(self.elf).section_by_entity(self)
        if self.location and self.section and self.associated_type:
            start = self.location - self.section.start
            end = start + ctypes.sizeof(self.associated_type.to_ctype())
            value = self.associated_type.to_ctype().from_buffer_copy(
                self.section.data()[start:end]
            )
        else:
            value = None
        self.value = value

    def __str__(self) -> str:
        if self.associated_type is None:
            return f"{self.name} <None at 0x00000000>"
        name = (
            f"{self.name} <{self.associated_type.class_name} at 0x{self.location:08x}>"
        )
        ret = f"{name}"
        return ret

    @abstractmethod
    def _derive_location(self) -> Optional[int]:
        ...

    def _derive_associated_type(self) -> Optional[Typeable]:
        attrs = self.die.attributes
        if "DW_AT_type" in attrs:
            return get_linked_type(self.die, self.elf)
        else:
            return None


class ExportableVariable(Protocol):
    name: str
    value: SupportsBytes


class Variable(Entity):
    """Supports `DW_TAG_variable` entries parsing"""

    SUPPORTED_TAGS = {"DW_TAG_variable"}
    associated_type: Typeable

    def _derive_location(self) -> Optional[int]:
        attrs = self.die.attributes
        if "DW_AT_location" not in attrs:
            return None
        location = attrs["DW_AT_location"]
        if location.form != "DW_FORM_exprloc":
            return None
        arr = location.value
        # Hardcoded parsing of DW_OP_addr, 0x03
        if arr[0] != 3:
            return None
        arr_ = arr[1:]
        try:
            value = int.from_bytes(arr_, byteorder="little", signed=False)
        except Exception:
            return None
        return value

    def _derive_associated_type(self) -> Typeable:
        attrs = self.die.attributes
        if "DW_AT_type" in attrs:
            return get_linked_type(self.die, self.elf)
        elif "DW_AT_specification" in attrs:
            return get_linked_type(
                get_linked_die_by_attr(self.die, "DW_AT_specification"), self.elf
            )
        else:
            raise NotImplementedError("variable type definition unknown")

    def to_python_code(self) -> str:
        if not self.name:
            raise ValueError("unable to generate python code for unnamed variable")
        if not self.value:
            raise ValueError(
                "unable to generate python code for variable without a value"
            )
        return cast(Typeable, self.associated_type).var_python_code(
            self.name, cast(ExportableVariable, self)
        )


class Subprogram(Entity):
    """Supports `DW_TAG_subprogram` entries parsing"""

    SUPPORTED_TAGS = {"DW_TAG_subprogram"}

    def __init__(self, die: _DIE, elf: _ELFFile) -> None:
        super().__init__(die, elf)
        self.args = self._derive_args()

    def _derive_location(self) -> Optional[int]:
        attrs = self.die.attributes
        if "DW_AT_low_pc" in attrs:
            location = attrs["DW_AT_low_pc"].value
            return location if location > 0 else None
        else:
            return None

    @staticmethod
    def _is_arg(arg: _DIE) -> bool:
        return arg.tag == "DW_TAG_formal_parameter"

    def _derive_args(self) -> Tuple[Typeable, ...]:
        return tuple(
            get_linked_type(c, self.elf)
            for c in filter(self._is_arg, self.die.iter_children())
        )


class DWARFParser:
    """DWARF data parser

    It is used for parsing DWARF data in ELFs with debug data.
    On :attr:`DWARFParser.parse` call, it walks through the whole DIE tree and calls
    method, named by it's tag.

    In case of the `DW_TAG_variable`, the parser searches for `parse_variable` method.
    If it has been implemented, it is called with the DIE instance as the first and the
    only argument.
    The method prototype is as follows::

        def parse_variable(self, die: DIE) -> Optional[bool]:
            ...

    In case the parsing method returns True, the parsing algorithm does not process
    current DIE's children.
    """

    def __init__(self, elf: _ELFFile) -> None:
        self._elf = elf

    def _parse_ctypes(self, die: _DIE) -> None:
        # TODO: Check the tag type
        name = f"parse_{die.tag[7:]}"
        if attr := getattr(self, name, None):
            if attr(die):
                return
        else:
            for child in die.iter_children():
                self._parse_ctypes(child)

    def parse(self):
        """Parse DIE tree"""
        d = self._elf.get_dwarf_info()
        for cu in d.iter_CUs():
            die = cu.get_top_DIE()
            self._parse_ctypes(die)


class DependencyGraph:
    """Class used to sort Typable dependencies"""

    _circular: bool

    def __init__(self, types: Iterable[Typeable]) -> None:
        self.input = [typ for typ in types]
        self._mapping = DefaultDict[Typeable, List[Typeable]](list)
        self.edge: Set[Typeable] = set()
        self._processed: Set[Typeable] = set()
        self._populate_mapping(self.input, set())

    def _populate_mapping(
        self, types: Iterable[Typeable], visited: Set[Typeable]
    ) -> None:
        for typ in types:
            if typ in visited:
                continue
            visited.add(typ)
            if isinstance(typ, DependentType) and (deps := typ.get_dependencies()):
                self._populate_mapping(deps, visited)
                for dep in deps:
                    self._mapping[dep].append(typ)
                continue
            self.edge.add(typ)

    @cached_property
    def has_circular(self) -> bool:
        """Whether the dependency graph has a circular dependency"""
        self.sorted
        return self._circular

    @staticmethod
    def _filter_sorted(ordered: List[Typeable]) -> List[Typeable]:
        name_set = set()
        output = []
        for typ in ordered:
            if typ.class_name not in name_set:
                name_set.add(typ.class_name)
                output.append(typ)
        return output

    @cached_property
    def sorted(self) -> List[Typeable]:
        """Sorts items by dependency

        :raises RuntimeError: in case a graph has a cyclic dependency
        :return: sorted typables by dependency
        """
        edge = self.edge.copy()
        ordered_set = set()
        ordered = []
        while edge:
            n = edge.pop()
            if n not in ordered_set:
                ordered_set.add(n)
                ordered.append(n)
            for m in list(self._mapping[n]):
                self._mapping[n].remove(m)
                if ordered_set.issuperset(cast(DependentType, m).get_dependencies()):
                    edge.add(m)
        self._circular = any(self._mapping.values())
        return self._filter_sorted(ordered)

    def _imports_util(self, type: Typeable) -> Iterable[str]:
        if isinstance(type, DependentType):
            for typ in type.get_dependencies():
                for imp in typ.get_python_imports():
                    yield imp
                yield from self._imports_util(typ)

    def get_imports(self) -> Iterable[str]:
        """An iterator of imports, used by all types of dependency graph

        :yield: import string
        """
        reported = set()
        for typ in self.input:
            for imp in self._imports_util(typ):
                if imp not in reported:
                    reported.add(imp)
                    yield imp


class AddressExtractor:
    """Address extractor from elf file extracts addresses by symbol name"""

    def __init__(self, elf: _ELFFile, names: Sequence[str]) -> None:
        self._elf = elf
        self._names = names

    def extract(self) -> Dict[str, int]:
        """Extract addresses from ELF file by the names, given to constructor

        :return: a dictionary of name-address pairs
        """
        return dict(
            map(
                self._symbol2location_map,
                filter(
                    self._filter,
                    (symbol for section in Sections(self._elf) for symbol in section),
                ),
            )
        )

    def _filter(self, s: _sections.Symbol) -> bool:
        return (s["st_info"]["type"] == "STT_OBJECT") and s.name in self._names

    @staticmethod
    def _symbol2location_map(s: _sections.Symbol) -> Tuple[str, int]:
        return s.name, s.entry.st_value


COMMENT = """\"\"\"Automatically generated with py_c_tools\"\"\""""


class Extractor(ABC):
    """Extractor base class"""

    _input_debug: pathlib.Path
    _input_release: pathlib.Path
    _output: pathlib.Path

    def __init__(
        self,
        input_dir: str,
        input_prefix: str,
        output_dir: Optional[str] = None,
        output_prefix: Optional[str] = None,
    ) -> None:
        """Valid input files are:

        Single debug `name.elf`
        Single debug `name_debug.elf`
        Debug `name_debug.elf` and release `name_release.elf` pair
        """
        in_dir = pathlib.Path(input_dir)
        if not in_dir.exists():
            raise ValueError("Input directory does not exist")
        if output_dir is not None:
            out_dir = pathlib.Path(output_dir)
            if not out_dir.exists():
                raise ValueError("Output directory does not exist")
        else:
            out_dir = in_dir
        in_dir_debug = in_dir / f"{input_prefix}_debug.elf"
        if not in_dir_debug.exists():
            in_dir_debug = in_dir / f"{input_prefix}.elf"
            if not in_dir_debug.exists():
                raise ValueError(
                    "Input ELF file prefix is invalid\n"
                    "  Could not find a debug - release pair"
                    "({0}_debug.elf and {0}_release.elf)\n"
                    "  nor a single debug file ({0}.elf)".format(input_prefix)
                )
            in_dir_release = in_dir_debug
        else:
            in_dir_release = in_dir / f"{input_prefix}_release.elf"
            if not in_dir_release.exists():
                in_dir_release = in_dir_debug
        self._input_debug = in_dir_debug
        self._input_release = in_dir_release
        self._output = out_dir / (
            f"{output_prefix if output_prefix is not None else input_prefix}.py"
        )

    @abstractmethod
    def extract(self) -> None:
        """Extracts the provided file(s) and writes to desired output

        Implementation should call :meth:`Extractor._write_file`.
        """
        raise NotImplementedError("method is not implemented")

    def _write_file(
        self,
        docstring: str = "",
        imports: Iterable[str] = (),
        body: str = "",
    ) -> None:
        formatted_imports = _isort.code("\n".join(imports))
        code = _black.format_str(
            "\n".join((docstring or COMMENT, formatted_imports, body)),
            mode=_black.Mode(),
        )
        with self._output.open("w") as f:
            f.write(code)


ERT = TypeVar("ERT")
ExportableEntry = Union[
    BaseType,
    PointerType,
    EnumerationType,
    Typedef,
    ArrayType,
    StructureType,
    UnionType,
    Subroutine,
    Variable,
    Subprogram,
]


class ExporterBase(Generic[ERT]):
    def __init__(self) -> None:
        self.__lookup: Dict[Type[ExportableEntry], Callable[[ExportableEntry], ERT]] = {
            BaseType: self._export_base_type,
            PointerType: self._export_pointer_type,
            EnumerationType: self._export_enumeration_type,
            Typedef: self._export_typedef,
            ArrayType: self._export_array_type,
            StructureType: self._export_structure_type,
            UnionType: self._export_union_type,
            Subroutine: self._export_subroutine_type,
            Variable: self._export_variable,
            Subprogram: self._export_subprogram,
            IntegralPaddingType: self._export_integral_padding_type,
            ArrayPaddingType: self._export_array_padding_type,
        }

    def export(self, entry: ExportableEntry) -> ERT:
        return self.__lookup[type(entry)](entry)

    @abstractmethod
    def _export_base_type(self, entry: BaseType) -> ERT:
        ...

    @abstractmethod
    def _export_pointer_type(self, entry: PointerType) -> ERT:
        ...

    @abstractmethod
    def _export_enumeration_type(self, entry: EnumerationType) -> ERT:
        ...

    @abstractmethod
    def _export_typedef(self, entry: Typedef) -> ERT:
        ...

    @abstractmethod
    def _export_array_type(self, entry: ArrayType) -> ERT:
        ...

    @abstractmethod
    def _export_structure_type(self, entry: StructureType) -> ERT:
        ...

    @abstractmethod
    def _export_union_type(self, entry: UnionType) -> ERT:
        ...

    @abstractmethod
    def _export_subroutine_type(self, entity: Subroutine) -> ERT:
        ...

    @abstractmethod
    def _export_variable(self, entry: Variable) -> ERT:
        ...

    @abstractmethod
    def _export_subprogram(self, entry: Subprogram) -> ERT:
        ...

    @abstractmethod
    def _export_integral_padding_type(self, entry: IntegralPaddingType) -> ERT:
        ...

    @abstractmethod
    def _export_array_padding_type(self, entry: ArrayPaddingType) -> ERT:
        ...


class XMLExporter(ExporterBase[_Element]):
    @staticmethod
    def _is_signed_str(
        type: Type[ctypes._SimpleCData],
    ) -> Union[Literal["true"], Literal["false"]]:
        return "true" if type(-1).value < 0 else "false"

    def _export_base_type(self, entry: BaseType) -> _Element:
        typ = entry.to_ctype()
        element = Element("base_type", None, None)
        element.set("name", entry.class_name)
        element.set("size", str(ctypes.sizeof(typ)))
        element.set("signed", self._is_signed_str(typ))
        return element

    def _export_pointer_type(self, entry: PointerType) -> _Element:
        typ = entry.to_ctype()
        element = Element("pointer_type", None, None)
        element.set("name", entry.class_name)
        element.set("size", str(ctypes.sizeof(typ)))
        return element

    def _export_enumeration_type(self, entry: EnumerationType) -> _Element:
        typ = entry.to_ctype()
        element = Element("enumeration_type", None, None)
        element.set("name", entry.class_name)
        element.set("size", str(ctypes.sizeof(typ)))
        for e in typ:
            child = Element("enum", None, None)
            child.set("name", e.name)
            child.set("value", str(e.value))
            element.append(child)
        return element

    def _export_typedef(self, entry: Typedef) -> _Element:
        element = Element("typedef", None, None)
        element.set("name", entry.class_name)
        element.set("type", entry.associated_type.class_name)
        return element

    def _export_array_type(self, entry: ArrayType) -> _Element:
        element = Element("array_type", None, None)
        element.set("name", entry.class_name)
        element.set("type", entry.associated_type.class_name)
        element.set("size", str(entry.shape))
        return element

    def _export_structure_type(self, entry: StructureType) -> _Element:
        typ = entry.to_ctype()
        element = Element("structure_type", None, None)
        element.set("name", entry.class_name)
        element.set("size", str(ctypes.sizeof(typ)))
        self.__add_element_members(element, entry)
        return element

    def _export_union_type(self, entry: UnionType) -> _Element:
        typ = entry.to_ctype()
        element = Element("union_type", None, None)
        element.set("name", entry.class_name)
        element.set("size", str(ctypes.sizeof(typ)))
        self.__add_element_members(element, entry)
        return element

    def _export_subroutine_type(self, entry: Subroutine) -> _Element:
        element = Element("subroutine_type", None, None)
        element.set("name", entry.class_name)
        return element

    def _export_variable(self, entry: Variable) -> _Element:
        element = Element("variable", None, None)
        if not entry.name:
            raise ValueError("Variable name is not known")
        element.set("name", entry.name)
        element.set("type", entry.associated_type.class_name)
        if entry.location:
            element.set("location", f"0x{entry.location:08x}")
        return element

    def _export_subprogram(self, entry: Subprogram) -> _Element:
        element = Element("subprogram", None, None)
        if not entry.name:
            raise ValueError("Subprogram name is not known")
        element.set("name", entry.name)
        if entry.associated_type:
            element.set("type", entry.associated_type.class_name)
        if entry.location:
            element.set("location", f"0x{entry.location:08x}")
        for a in entry.args:
            child = Element("arg", None, None)
            child.set("type", a.class_name)
            element.append(child)
        return element

    def _export_integral_padding_type(self, entry: IntegralPaddingType) -> _Element:
        typ = entry.to_ctype()
        element = Element("integral_padding_type", None, None)
        element.set("name", entry.class_name)
        element.set("size", str(ctypes.sizeof(typ)))
        return element

    def _export_array_padding_type(self, entry: ArrayPaddingType) -> _Element:
        element = Element("array_padding_type", None, None)
        element.set("name", entry.class_name)
        element.set("size", str(entry.shape))
        return element

    @staticmethod
    def __add_element_members(
        e: _Element, entry: Union[UnionType, StructureType]
    ) -> None:
        for m in entry.members:
            child = Element("member", None, None)
            child.set("name", m.name)
            child.set("type", m.type.class_name)
            if m.bit_length is not None:
                child.set("bitlength", str(m.bit_length))
            e.append(child)
