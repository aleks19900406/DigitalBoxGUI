import argparse
import os

from .core import IOParamExtractor

PARSER = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description="Tool for static 'io_param_t' instance structure translation",
    epilog="If input directory is not provided, the cwd will be used.\n"
    "If output directory is not provided, the input directory will be used.\n"
    "If output is not provided, input will be used.\n",
)
PARSER.add_argument("--input", "-i", required=True, type=str, help="Input ELF prefix")
PARSER.add_argument("--output", "-o", default=None, type=str, help="Input ELF prefix")
PARSER.add_argument(
    "--in_dir", "-I", default=os.getcwd(), type=str, help="Directory of the ELF file(s)"
)
PARSER.add_argument(
    "--out_dir",
    "-O",
    default=None,
    type=str,
    help="Directory of the output python file",
)

ARGS = PARSER.parse_args()
EXTRACTOR = IOParamExtractor(ARGS.in_dir, ARGS.input, ARGS.out_dir, ARGS.output)
EXTRACTOR.extract()
