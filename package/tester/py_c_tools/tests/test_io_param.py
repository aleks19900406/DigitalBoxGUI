import os
from unittest import TestCase
from pathlib import Path
from importlib import util

from c_tools.specializations.io_param.core import IOParamExtractor


class TestIOParam(TestCase):
    f_name = "io_param_test"
    path = Path(__file__).parent / "data"
    module_path = path / f"{f_name}.py"

    @classmethod
    def tearDownClass(cls) -> None:
        if cls.module_path.exists:
            os.remove(str(cls.module_path))

    def test_01_extract(self):
        extractor = IOParamExtractor(str(self.path), self.f_name)
        extractor.extract()

    def test_02_load(self):
        spec = util.spec_from_file_location("param", str(self.module_path))
        if spec is None:
            self.fail("spec could not be created from file")
        try:
            param = util.module_from_spec(spec)
            spec.loader.exec_module(param)
        except Exception:
            self.fail("Errornous module code")
        attr = "REQUEST_READ"
        self.assertTrue(hasattr(param, attr), f"Missing {attr}")
