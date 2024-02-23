import pathlib
import re
import subprocess
from enum import Enum
from typing import Optional, Sequence, Tuple, Union


class SubprocessError(subprocess.SubprocessError):
    """Subprocess error"""
    def __init__(self, error_code: int, *args: object) -> None:
        self.error_code = error_code
        super().__init__(*args)


def find_bracket_range(s: str, idx: int) -> Tuple[int, int]:
    inside = False
    start = 0
    stack = []
    for n, char in enumerate(s[idx:]):
        if char in find_bracket_range.opening:
            if not inside:
                start = idx + n
            inside = True
            stack.append(find_bracket_range.mapping[char])
        elif char in find_bracket_range.closing:
            if not inside or char != stack.pop():
                break
        if inside and not stack:
            return start, idx + n
    raise ValueError("non-matching brackets")


find_bracket_range.opening = tuple("([{")
find_bracket_range.closing = tuple(")]}")
find_bracket_range.mapping = dict(
    zip(find_bracket_range.opening, find_bracket_range.closing)
)


class Preprocessor:
    """Preprocessor class to be used for c file preprocessing

    `gcc` is used for preprocessing so it must be available in path.

    :param include_dirs: a list of direcotries, containing includes
    """
    class Mode(Enum):
        RAW = ""
        COMMENT = "comment"

    OPTS = {Mode.RAW: (), Mode.COMMENT: ("-C",)}

    def __init__(self, include_dirs: Sequence[pathlib.Path]) -> None:
        self._include_dirs = [str(i) for i in include_dirs]

    def _remove_gcc_keywords(self, s: str) -> str:
        removals = []
        for match in re.finditer(r"__attribute__\(\(", s):
            start = match.start()
            _, end = find_bracket_range(match.string, start)
            removals.append((start, end))
        for rng in reversed(removals):
            s = s[: rng[0]] + s[rng[1] + 1 :]
        return s

    def preprocess_file(
        self, file: str, mode: Optional[Union["Preprocessor.Mode", str]]
    ) -> str:
        """Preprocesses a given file with desired preprocessing mode

        :param file: file to preprocess
        :param mode: desired preprocessing mode
        :raises ValueError: in case of unsupported preprocessing mode
        :raises RuntimeError: in case of subprocess failure
        :return: preproccessed source file
        """
        try:
            mode = self.Mode(mode)
        except ValueError:
            raise ValueError("unsupported preprocessor mode") from None
        command = [
            "gcc",
            "-E",
            "-P",
            *self.OPTS[mode],
            *(i for j in (("-I", d) for d in self._include_dirs) for i in j),
            file,
        ]
        ret = subprocess.run(
            command,
            capture_output=True,
        )
        if ret.returncode:
            raise RuntimeError(ret.returncode, ret.stderr.decode())
        s = ret.stdout.decode()
        s = s.replace("\r", "")
        return self._remove_gcc_keywords(s)
