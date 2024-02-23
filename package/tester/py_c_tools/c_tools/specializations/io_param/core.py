from enum import IntFlag as _IntFlag
from itertools import chain
from typing import DefaultDict, Dict, List, Optional, cast

from elftools.dwarf.die import DIE as _DIE
from elftools.elf.elffile import ELFFile as _ELFFile

from c_tools.parser import elf as _ep

# region Constants
DEFINES = """
RPC_READ = 0x83
RPC_WRITE = 0xab

IO_PARAM_PROTOCOL_ID = 0x12345678
"""
CALL_HEADER = """class RemoteCallHeader(c_tools.parser.utils.CtypesLEStruct):
    _pack_ = 1
    _fields_ = [
        ("pad", ctypes.c_uint8),
        ("protocol_id", ctypes.c_uint32),
        ("call_type", ctypes.c_uint32)
    ]
"""
REQ_READ_CLASS = """class RequestRead(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("header", RemoteCallHeader),
        ("payload", ctypes.c_uint32 * {size})  # Number of readable IOParams
    ]
"""
RESP_READ_CLASS = """class ResponseRead(ctypes.LittleEndianStructure):
    _pack_ = True
    _fields_ = [
        ("header", ctypes.c_uint32),
        {members}
    ]
"""
REQ_READ_FORMAT = """REQUEST_READ = RequestRead(
    (0, IO_PARAM_PROTOCOL_ID, RPC_READ),
    (
        {addresses}
    )
)"""
# endregion Constants


class IOParam:
    """io_param_t information representation"""

    class Mode(_IntFlag):
        N = 0
        R = 1
        W = 2

    def __init__(self) -> None:
        self._var: Optional[_ep.Variable] = None
        self._getter: Optional[_ep.Subprogram] = None
        self._setter: Optional[_ep.Subprogram] = None
        self._getter_type: Optional[_ep.Typeable] = None
        self._setter_type: Optional[_ep.Typeable] = None

    def __str__(self) -> str:
        if self._var:
            name = self._var.name if self._var else "None"
            loc = self._var.location
        else:
            name = "None"
            loc = 0
        return f"<{name:20} at 0x{loc:08x} with mode {self.mode}>"

    @property
    def var(self) -> Optional[_ep.Variable]:
        return self._var

    @var.setter
    def var(self, var: _ep.Variable) -> None:
        if self._var is None:
            self._var = var
        elif self._var != var:
            raise ValueError("incompatible variables")

    @property
    def getter(self) -> Optional[_ep.Subprogram]:
        return self._getter

    @getter.setter
    def getter(self, getter: _ep.Subprogram) -> None:
        if self._getter is None:
            self._getter_type = self._validate_callback(getter)
            self._getter = getter
        else:
            raise RuntimeError("getter is already set")

    @property
    def setter(self) -> Optional[_ep.Subprogram]:
        return self._setter

    @setter.setter
    def setter(self, setter: _ep.Subprogram) -> None:
        if self._setter is None:
            self._setter_type = self._validate_callback(setter)
            self._setter = setter
        else:
            raise RuntimeError("setter is already set")

    @property
    def mode(self) -> "IOParam.Mode":
        return self.Mode(bool(self.getter) + (bool(self.setter) << 1))

    @property
    def getter_type(self) -> Optional[_ep.Typeable]:
        if self._getter and not self._getter_type:
            raise ValueError("getter set, but getter type is None")
        return self._getter_type

    @property
    def setter_type(self) -> Optional[_ep.Typeable]:
        if self._setter and not self._setter_type:
            raise ValueError("setter set, but setter type is None")
        return self._setter_type

    def _validate_callback(self, cb: _ep.Subprogram) -> _ep.Typeable:
        args = cb.args
        if len(args) != 1:
            raise ValueError("invalid number of arguments")
        arg = args[0]
        if not isinstance(arg, _ep.PointerType):
            raise TypeError("argument should be a pointer")
        at = arg.associated_type
        if at is None:
            raise ValueError(
                "pointer type should be known{}".format(
                    f" for type {self.var.name}" if self.var else ""
                )
            )
        return at

    def is_valid(self) -> bool:
        if self._var is None:
            return False
        if self._var.name is None:
            return False
        if self._setter and (self._setter_type is None):
            return False
        if self._getter and (self._getter_type is None):
            return False
        return True


class IOParamParser(_ep.DWARFParser):
    """IO parameter parser"""

    def __init__(self, elf: _ELFFile) -> None:
        self._params = None
        self.variables: List[_ep.Variable] = []
        self.getters = DefaultDict[int, List[_ep.Variable]](list)
        self.setters = DefaultDict[int, List[_ep.Variable]](list)
        self.functions: List[_ep.Subprogram] = []
        super().__init__(elf)

    def _populate_io_params(self):
        per_var = DefaultDict[_ep.Variable, IOParam](IOParam)
        for f in self.functions:
            g = self.getters.get(f.location, [])
            s = self.setters.get(f.location, [])
            for i in g:
                per_var[i].var = i
                per_var[i].getter = f
            for i in s:
                per_var[i].var = i
                per_var[i].setter = f
        self._params = list(filter(IOParam.is_valid, per_var.values()))

    def parse_variable(self, die: _DIE) -> bool:
        var = _ep.Variable(die, self._elf)
        at = var.associated_type
        if at and at.name == "io_param_t":
            self.variables.append(var)
            if var.value.get:
                self.getters[var.value.get & ~1].append(var)  # Mode switch
            if var.value.set:
                self.setters[var.value.set & ~1].append(var)
        return True

    def parse_subprogram(self, die: _DIE) -> bool:
        self.functions.append(_ep.Subprogram(die, self._elf))
        return True

    def parse(self):
        super().parse()
        self._populate_io_params()

    @property
    def params(self) -> List[IOParam]:
        """Could take quite some time the first time for parser to do his work"""
        if self._params is None:
            self.parse()
        return cast(List[IOParam], self._params)

    @property
    def readable_params(self) -> List[IOParam]:
        return [param for param in self.params if IOParam.Mode.R in param.mode]

    @property
    def writable_params(self) -> List[IOParam]:
        return [param for param in self.params if IOParam.Mode.W in param.mode]


class IOParamExtractor(_ep.Extractor):
    def extract(self):
        with open(self._input_debug, "rb") as f:
            elf = _ELFFile(f)
            params = self._extract_readable(elf)
            dg = _ep.DependencyGraph(
                cast(_ep.Typeable, var.getter_type) for var in params
            )
            sort = dg.sorted
        with open(self._input_release, "rb") as f:
            elf = _ELFFile(f)
            address_map = _ep.AddressExtractor(
                elf, [cast(str, p.var.name) for p in params]
            ).extract()
        self._to_file(dg, sort, params, address_map)

    def _extract_readable(self, elf: _ELFFile) -> List[IOParam]:
        parser = IOParamParser(elf)
        return parser.readable_params

    def _to_file(
        self,
        dg: _ep.DependencyGraph,
        sort: List[_ep.Typeable],
        params: List[IOParam],
        address_map: Dict[str, int],
    ) -> None:
        req_read_class = REQ_READ_CLASS.format(size=len(params))
        resp_read_class = RESP_READ_CLASS.format(
            members="\n        ".join(
                f'("{param.var.name}", {param.getter_type.class_name}),'
                for param in params
            )
        )
        req_read_format = REQ_READ_FORMAT.format(
            addresses="\n        ".join(
                "0x{{{0}:08x}},  # {0}".format(param.var.name) for param in params
            )
        )
        req_read = req_read_format.format(**address_map)
        types = "\n".join(typ.to_python_code() for typ in sort)
        implementation = "\n".join(
            (DEFINES, CALL_HEADER, req_read_class, resp_read_class, req_read)
        )
        body = "\n".join((types, implementation))
        imports = (
            f"import {i}" for i in chain(dg.get_imports(), ("c_tools.parser.utils",))
        )
        super()._write_file(imports=imports, body=body)
