from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Optional, Sequence

from .parser.code import TypeParser
from .preprocessor import Preprocessor


def c_import(
    file_path: str,
    includes: Sequence[str],
    globals: Dict[str, Any],
    name: Optional[str] = None,
) -> ModuleType:
    """Imports c source file as python module

    Newly created module is registered in globals by the given name and returned.

    :param file_path: c source file path
    :param includes: a list of include directories
    :param globals: dictionary of globals to put the module in
    :param name: desired name of the module. If not specified the source file stem is
                 used instead.
    :return: newly created module
    """
    path = Path(file_path).absolute()
    module_name = name or path.stem
    preprocessor = Preprocessor([Path(i) for i in includes])
    text = preprocessor.preprocess_file(str(path), Preprocessor.Mode.RAW)
    main_module = TypeParser().parse(text, module_name)
    globals[module_name] = main_module
    return main_module
