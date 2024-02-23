# TODO: Add doscstring
from dataclasses import dataclass
from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import Dict, Optional, Set, Type, Union, cast
from warnings import warn

from elftools.dwarf.die import DIE
from elftools.elf.elffile import ELFFile
from elftools.elf.sections import Symbol, SymbolTableSection
from lxml import etree
from lxml.etree import Element, _Element
from pyquery import PyQuery

from c_tools.parser.elf import (
    DependencyGraph,
    DWARFParser,
    Entry,
    ExportableVariable,
    Extractor,
    Subprogram,
    Typeable,
    Typedef,
    Variable,
    XMLExporter,
    die_name2class_name,
)


class FilterTypeByName:
    def __init__(self):
        self.names = set()

    def __call__(self, item):
        if item.name in self.names:
            return False
        self.names.add(item.name)
        return True


@dataclass
class VariableEntry:
    xml: _Element
    elf: Optional[Variable] = None
    address: Optional[int] = None


@dataclass
class VariableModuleEntry:
    description: str
    variables: Dict[str, VariableEntry]


@dataclass
class FunctionEntry:
    xml: _Element
    elf: Optional[Subprogram] = None
    argument: str = ""
    address: Optional[int] = None


@dataclass
class FunctionModuleEntry:
    description: str
    functions: Dict[str, FunctionEntry]


class MATParser(DWARFParser):

    XML_ROOT = "protocol"
    COMMAND_MODULES_SELECTOR = (
        f'{XML_ROOT}>commands>command_group[name="{{}}"]>modules'
    )
    COMMAND_SELECTOR = COMMAND_MODULES_SELECTOR + ">module"

    class CommandType(Enum):
        GET_VAR = "GET VALUES FROM RAM"  # Get values from ram
        CALL_FUNCTION = "START SUBMODULES"  # Call function by pointer

    def __init__(self, xml: PyQuery, elf: ELFFile) -> None:
        super().__init__(elf)
        self._xml = xml
        # A collection of variables used by GET_VALUES_FROM_RAM command
        self.variables: Dict[str, VariableModuleEntry] = {
            i.get("name"): VariableModuleEntry(
                i.get("description"),
                {j.get("name"): VariableEntry(j) for j in i.getchildren()},
            )
            for i in self._xml(
                self.COMMAND_SELECTOR.format(self.CommandType.GET_VAR.value)
            )
        }
        # A collection of functions used by CALL_FUNCTION_BY_POINTER command
        self.functions: Dict[str, FunctionModuleEntry] = {
            i.get("name"): FunctionModuleEntry(
                i.get("description"),
                {j.get("name"): FunctionEntry(j) for j in i.getchildren()},
            )
            for i in self._xml(
                self.COMMAND_SELECTOR.format(self.CommandType.CALL_FUNCTION.value)
            )
        }
        # A collection of types used
        self._needed_types: Set[str] = set()
        for _, module_data in self.variables.items():
            for _, variable_data in module_data.variables.items():
                associated_type_str = variable_data.xml.get("associated_type", None)
                if associated_type_str is None:
                    continue
                for type_name in associated_type_str.split(":"):
                    if type_name:
                        self._needed_types.add(type_name)
        for _, module_data in self.functions.items():
            for _, function_data in module_data.functions.items():
                type_name = function_data.xml.get("argument_type", None)
                if type_name:
                    self._needed_types.add(type_name)
        # Modules to be visited when parsing - non present names will be skipped
        self.modules = self.variables.keys() | self.functions.keys()
        # Holds every used type names. Be sure to add a type in the parser method
        self.parsed_types = set()

    def parse_variable(self, die: DIE) -> None:
        module_name = self.get_cu_name(die.cu.get_top_DIE())
        variables_data = self.variables.get(module_name, None)
        if variables_data is None:
            return
        try:
            if (
                die.attributes["DW_AT_name"].value.decode()
                not in variables_data.variables
            ):
                return
            v = Variable(die, self._elf)
            variables_data.variables[cast(ExportableVariable, v).name].elf = v
            self.parsed_types.add(v.associated_type)
        except Exception as e:
            warn(
                f"Variable without a name in module {module_name}? ({e})",
            )

    def parse_typedef(self, die: DIE) -> None:
        current_module_name = self.get_cu_name(die.cu.get_top_DIE())
        try:
            self._parse_type(die)
        except Exception as e:
            warn(
                f"Typedef without a name in module {current_module_name}? ({e})",
            )

    def _parse_type(self, die: DIE) -> None:
        name = die.attributes.get("DW_AT_name", None)
        if name is None or name.value.decode() not in self._needed_types:
            return
        self.parsed_types.add(Entry.get(die, self._elf))

    def parse_subprogram(self, die: DIE) -> None:
        module_name = self.get_cu_name(die.cu.get_top_DIE())
        module_data = self.functions.get(module_name, None)
        if module_data is None:
            return
        try:
            if die.attributes["DW_AT_name"].value.decode() in module_data.functions:
                f = Subprogram(die, self._elf)
                function_data = module_data.functions[f.name]
                function_data.elf = f
                arguments = f.args
                n_arguments = len(arguments)
                if n_arguments == 1:
                    arg_name = function_data.xml.get("argument_type", None)
                    function_data.argument = die_name2class_name(arg_name or "")
                else:
                    warn(f"Invalid number of function arguments ({n_arguments})")
        except Exception as e:
            warn(
                f"Subprogram without a name in module {module_name}? ({e})",
            )

    def parse(self):
        d = self._elf.get_dwarf_info()
        for cu in d.iter_CUs():
            die = cu.get_top_DIE()
            #name = self.get_cu_name(die)
            #if name not in self.modules:
            #    continue
            self._parse_ctypes(die)
        self._validate()
        self._set_locations()
        self.parsed_types = set(filter(FilterTypeByName(), self.parsed_types))

    def _validate(self) -> None:
        self._validate_variables()
        self._validate_subprograms()

    def _validate_variables(self) -> None:
        for module_name, var_entry in self.variables.items():
            for var_name, var in var_entry.variables.items():
                if var.elf is None:
                    warn(
                        f"Variable {var_name} was not found in module {module_name}?",
                    )

    def _validate_subprograms(self) -> None:
        for module_name, func_entry in self.functions.items():
            for func_name, func in func_entry.functions.items():
                if func.elf is None:
                    warn(
                        f"Function {func_name} was not found in module {module_name}?",
                    )

    def _set_locations(self) -> None:
        ...

    @staticmethod
    def get_cu_name(die: DIE) -> str:
        file = Path(die.cu.get_top_DIE().attributes["DW_AT_name"].value.decode())
        return file.stem


class MATExtractor(Extractor):
    def __init__(
        self,
        input_dir: str,
        input_prefix: str,
        output_dir: Optional[str] = None,
        output_prefix: Optional[str] = None,
    ) -> None:
        super().__init__(input_dir, input_prefix, output_dir, output_prefix)
        self._input_xml = Path(input_dir) / f"{input_prefix}.xml"
        self._output_xml = self._output.parent / (self._output.stem + ".xml")
        if self._output_xml == self._input_xml:
            self._output_xml = self._output_xml.parent / (
                self._output_xml.stem + "_output.xml"
            )
        with open(self._input_xml, "rb") as f:
            self._xml = etree.fromstring(f.read())
        self._elf_file_handle = open(self._input_debug, "rb")
        self._elf = ELFFile(self._elf_file_handle)

    def __del__(self):
        if hasattr(self, "_elf_file_handle"):
            self._elf_file_handle.close()

    @staticmethod
    def _populate_variables(modules: _Element, parser: MATParser) -> None:
        modules.clear(False)
        for module_name, module_data in parser.variables.items():
            module = Element("module", None, None)
            module.set("name", module_name)
            module.set("description", module_data.description)
            for variable_name, variable_data in module_data.variables.items():
                if variable_data.elf is None:
                    raise NameError(f"Variable '{variable_name}' was not found in '{module_name}'")
                variable: _Element = Element("variable", None, None)
                variable.set("name", variable_name)
                if variable_data.elf.associated_type is None:
                    raise TypeError(f"Variable '{variable_name}' type could not be derived.")
                var_type = variable_data.elf.associated_type
                variable.set("type", var_type.class_name)
                location = variable_data.address
                variable.set(
                    "location", f"0x{location:08x}" if location else "optimized out"
                )
                variable.set("description", variable_data.xml.get("description", ""))
                for member in variable_data.xml.iterchildren():
                    variable.append(member)
                module.append(variable)
            modules.append(module)

    @staticmethod
    def _populate_functions(modules: _Element, parser: MATParser) -> None:
        modules.clear(False)
        for module_name, module_data in parser.functions.items():
            module: _Element = Element("module", None, None)
            module.set("name", module_name)
            module.set("description", module_data.description)
            for function_name, function_data in module_data.functions.items():
                if function_data.elf is None:
                    raise NameError(f"Function '{function_name}' was not found in '{module_name}'")
                function = Element("function", None, None)
                function.set("name", function_name)
                function.set("argument_type", function_data.argument)
                location = function_data.address
                function.set(
                    "location", f"0x{location:08x}" if location else "optimized out"
                )
                function.set("description", function_data.xml.get("description", ""))
                module.append(function)
            modules.append(module)

    def _correct_addresses(
        self,
        variables: Dict[str, VariableEntry],
        functions: Dict[str, FunctionEntry],
    ) -> None:
        sections = (
            s for s in self._elf.iter_sections() if isinstance(s, SymbolTableSection)
        )
        symbols = (s for sect in sections for s in sect.iter_symbols())
        for s in symbols:
            t = s["st_info"]["type"]
            if t == "STT_FUNC":
                self._correct_address(functions, s)
            elif t == "STT_OBJECT":
                self._correct_address(variables, s)

    def _correct_address(
        self,
        entries: Union[Dict[str, FunctionEntry], Dict[str, VariableEntry]],
        symbol: Symbol,
    ) -> None:
        entry = entries.get(symbol.name, None)
        if entry is None:  # Not an object of interest
            return
        entry.address = symbol["st_value"]


    def extract(self):
        pq = PyQuery(self._xml)
        parser = MATParser(pq, self._elf)
        parser.parse()
        dg = DependencyGraph(parser.parsed_types)
        variables = {
            k: v for vm in parser.variables.values() for k, v in vm.variables.items()
        }
        functions = {
            k: v for vm in parser.functions.values() for k, v in vm.functions.items()
        }
        self._correct_addresses(variables, functions)
        exporter = XMLExporter()
        variable_modules = PyQuery(self._xml)(
            parser.COMMAND_MODULES_SELECTOR.format(parser.CommandType.GET_VAR.value)
        )
        if len(variable_modules) == 1:
            self._populate_variables(variable_modules[0], parser)
        function_modules = pq(
            parser.COMMAND_MODULES_SELECTOR.format(
                parser.CommandType.CALL_FUNCTION.value
            )
        )
        if len(function_modules) == 1:
            self._populate_functions(function_modules[0], parser)
        types = Element("types", None, None)
        for entry in dg.sorted:
            types.append(exporter.export(entry))
        self._xml.append(types)
        # Write file
        parser = etree.XMLParser(remove_blank_text=True)
        file = BytesIO(etree.tostring(self._xml))
        tree = etree.parse(file, parser)
        tree.write(str(self._output_xml), pretty_print=True)
        return self._xml
