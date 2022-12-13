"""Functions for searching files by tag, sheets of excel file by name...

.. module:: helpers.imaging
    :synopsis: Module consists of functions for searching files by tag, sheets of excel
               file by name...

.. modluauthor: Marko Vačovnik <marko.vacovnik@gorenje.com>

"""
import os
from numbers import Real
from typing import Dict, List, Optional, Union

import cv2
import numpy as np
import regex as re
import xlrd



class MalformedFileError(Exception):
    """Added for signalling malformed file exceptions """


def file_by_tag(path: str, tag: str, exception: bool = True) -> Union[str, None]:
    """Finds the tagged file in path by the tag parameter. Raises exception if not
    found.

    :param path: path to search for tagged file in
    :param tag: tag of the file to search by
    :param exception: whether to raise an exception in case no file was found
    :raise FileNotFoundError: in case no file was found and exception is True
    :return: the first matching file

    Files must be formatted as described in :ref:`file-by-tag`.
    """
    for f in os.listdir(path):
        fn = os.path.splitext(f)[0]
        if tag in set(fn.split("-")):
            return f
    if exception:
        raise FileNotFoundError(
            f"file with tag '{tag}' does not exist in path '{path}'"
        )
    return None


def file_by_extension(
    path: str, extension: str, exception: bool = True
) -> Union[str, None]:
    """Finds the first file with given extension in path. Raises exception if not
    found.

    :param path: path to search for file in
    :param extension: extension of the file to search by
    :param exception: whether to raise an exception in case no file was found
    :raise FileNotFoundError: in case no file was found
    :return: the first matching file

    """
    for f in os.listdir(path):
        if os.path.splitext(f)[-1] == ("." + extension):
            return f
    if exception:
        raise FileNotFoundError(
            f"file with extension '{extension}' does not exist in path '{path}'"
        )
    return None


def file_by_tag_and_extension(
    path: str, tag: str, extension: str, exception: bool = True
) -> Union[str, None]:
    """Finds the file by tag and extension in path. Raises exception if not found.

    :param path: path for search for file in
    :param tag: tag of the file to search by
    :param extension: extension of the file to search by
    :param exception: whether to raise an exception in case no file was found,
                      defaults to True
    :raises FileNotFoundError: in case no file was found
    :return: matching file

    .. seealso:: :func:`file_by_tag` and :func:`file_by_extension`
    """
    regex = r"^(?:([a-zA-Z0-9_ ]*)-)*{}(?:-([a-zA-Z0-9_ ]*))*\.{}$".format(
        tag, extension
    )
    r = re.compile(regex)
    for f in os.listdir(path):
        if r.match(f):
            return os.path.join(os.path.realpath(path), f)
    if exception:
        raise FileNotFoundError(
            f"file with tag '{tag}' and extension '{extension}'"
            + f" does not exist in path '{path}'"
        )
    return None


def sheet_by_tag(
    workbook: xlrd.Book, tag: str, exception: bool = True
) -> Optional[int]:
    """Finds the tagged sheet in the excel workbook by the tag parameter

    :param workbook: xlrd workbook to find the sheet in
    :param tag: tag of the sheet to search for
    :param exception: whether to raise an exception in case no sheet was found
    :return: index of the first sheet, matching tag if exists, else None

    Tags must be formatted as described in :ref:`sheet-by-tag`.
    """
    try:
        return min(
            [i for i, j in enumerate(workbook.sheet_names()) if tag in j.split("-")]
        )
    except ValueError:
        if exception:
            raise KeyError(f"there is no sheet tagged with '{tag}'")
        return None




def sheet_to_dict(
    worksheet: xlrd.sheet.Sheet, start: int = 0, end: Optional[int] = None
) -> Dict[str, str]:
    """Transforms the worksheet to dictionary

    :param worksheet: xlrd worksheet to extract a dictionary from
    :param start: starting row of the extraction (included)
    :param end: ending row of the extraction (excluded)
    :raise MalformedFileError: in case the worksheet has multiple values under the
                               single key
    :return: parsed dictionary

    Sheet must be formatted as described in :ref:`sheet-to-dict`.
    """
    key_col = 0
    value_col = 1
    ret = {}
    if end is None:
        end = worksheet.nrows
    for row in range(start, end):
        key = worksheet.cell_value(row, key_col)
        value = worksheet.cell_value(row, value_col)
        if key in ret.keys():
            raise MalformedFileError(f"multiple values for single key ({key})")
        else:
            ret[key] = value
    return ret




XlCellValueType = Union[str, Real]


def tabular_sheet_to_dict(
    worksheet: xlrd.sheet.Sheet,
) -> Dict[XlCellValueType, Dict[XlCellValueType, XlCellValueType]]:
    """Transforms a tabular sheet to dict of dicts.

    :param worksheet: xlrd worksheet to extract a dictionary from
    :return: dict of dicts

    Dict is constructed by keys from the first (0) column (starting in row 1) and values
    as dicts with keys from the first (0) row (starting in column 0).

    Sheet must be formatted as described in :ref:`tabular-sheet-to-dict`.
    """
    return {
        worksheet.cell(i, 0).value: {
            worksheet.cell(0, j).value: worksheet.cell(i, j).value
            for j in range(1, worksheet.ncols)
        }
        for i in range(1, worksheet.nrows)
    }


def load_image(file_path: str) -> np.ndarray:
    """Loads image from file path and returns numpy array in RGB888 color format

    :param file_path: image file path
    :return: image as RGB888 numpy array

    Supports 3 channel images.
    """
    try:
        return cv2.cvtColor(cv2.imread(file_path), cv2.COLOR_BGR2RGB)
    except cv2.error:
        raise FileNotFoundError(f"image {file_path} does not exist")


def save_image(file_path: str, image: np.ndarray) -> None:
    """Saves image to file path

    :param file_path: image file path
    :param image: image as RGB888 numpy array
    """
    if not cv2.imwrite(file_path, cv2.cvtColor(image, cv2.COLOR_RGB2BGR)):
        raise RuntimeError("Unable to save image")
