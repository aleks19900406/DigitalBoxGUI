from unittest import TestCase
from pathlib import Path
from c_tools import c_import


class TestImport(TestCase):
    def test_01_import_from_code(self):
        module_name = "my_module_name"
        module = c_import(
            Path(__file__).parent / "parser" / "data" / "source_test.c",
            [],
            locals(),
            module_name,
        )
        self.assertIn(module_name, locals())
        my_module = locals()[module_name]
        self.assertEqual(module, my_module)
