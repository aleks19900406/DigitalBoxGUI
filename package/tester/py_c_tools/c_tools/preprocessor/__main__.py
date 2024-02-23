import argparse
import pathlib
from typing import Set

from ._core import Preprocessor, SubprocessError


def existing_path(s: str) -> pathlib.Path:
    p = pathlib.Path(s).absolute()
    if not p.exists():
        raise argparse.ArgumentTypeError(f"\n'{s}' does not exist")
    return p


def non_existing_path(s: str) -> pathlib.Path:
    p = pathlib.Path(s).absolute()
    if p.exists():
        raise argparse.ArgumentTypeError(f"\n'{s}' exists")
    return p


class CommonFileTypeValidator:
    def __init__(self, possible_extensions: Set[str]) -> None:
        self._ext = None
        self._exts = set(possible_extensions)

    def _validate_ext(self, p: pathlib.Path, s: str) -> None:
        if self._ext is None:
            if p.suffix not in self._exts:
                raise argparse.ArgumentTypeError(f"\n'{s}' has invalid file type")
            self._ext = p.suffix
        else:
            if p.suffix != self._ext:
                raise argparse.ArgumentTypeError(
                    f"\n'{s}' is of inconsistent file type"
                )

    def valid_output_file(self, s: str) -> pathlib.Path:
        p = pathlib.Path(s).absolute()
        self._validate_ext(p, s)
        return p

    def valid_input_file(self, s: str) -> pathlib.Path:
        p = existing_path(s)
        self._validate_ext(p, s)
        return p


file_validator = CommonFileTypeValidator(
    {
        ".c",
    }
)
parser = argparse.ArgumentParser(
    prog="",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description="Tool for preproccessing c source files",
)
parser.add_argument(
    "--include-dirs",
    "-I",
    nargs=argparse.ZERO_OR_MORE,
    type=existing_path,
    help="a list of include directories",
)
parser.add_argument(
    "--output-file",
    "-o",
    type=file_validator.valid_output_file,
    required=True,
    help="",
)
parser.add_argument(
    "--input-file",
    "-i",
    type=file_validator.valid_input_file,
    help="file to run preprocessor on",
)

args = parser.parse_args()

path = args.output_file
preprocessor = Preprocessor(args.include_dirs)
for i in (Preprocessor.Mode.RAW, Preprocessor.Mode.COMMENT):
    try:
        text = preprocessor.preprocess_file(str(args.input_file), i)
    except SubprocessError as e:
        print(e)
        exit(e.error_code)
    fname = path.parent / f"{path.stem}{'_' if i.value else ''}{i.value}{path.suffix}"
    with fname.open(mode="w", newline="") as f:
        f.write(text)
