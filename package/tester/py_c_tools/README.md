# Welcome to 'c_tools' package repository!

## Quick overview

Project consists of tools for c code analysis mainly used for appliance testing.

## Installation

At first the dependencies must be installed in the working environment by executing

    pip install -r requirements.txt

After that, one can simply install the package by running

    python setup.py install
or

    pip install .
in the root of repository tree.

## Usage

The module is used to translate c structures and types to python ctypes objects.
Some use cases are represented below.

## Parsing source files

Let's take the following c objects:

```c
typedef enum _day
{
    Monday,
    Tuesday,
    Wednesday,
    Thursday,
    Friday,
    Saturday,
    Sunday
} day;

typedef struct uart {
    int fd;
    day d;
    char rx_buff[1024];
    char tx_buff[1024];
} uart_t;
```

It is possible to use the parsed objects as structures:

```python
from c_tools.parser.code import TypeParser

with open(file_name, "w") as f:
    text = f.read()
parser = TypeParser()
module = parser.parse(text)

uart = module.uart_t()  # New uart structure with typedef
uart = module.struct.uart()  # The same thing without typedef
uart.fd = 100
uart.d = module.day.Monday  # Using enum typedef
uart.d = module.enum._day.Monday  # Using enum without typedef
uart.rx_buff = b"rx buffer values"

uart_bytes = bytes(uart)  # Translate uart structure to bytes

uart1 = module.uart_t.from_buffer_copy(b"1234... 1234")  # Structure from bytes
```

C file may also be imported as module like:
```python
from c_tools import c_import

c_import(c_file_path, [include_path1, include_path2], globals(), "module_name")
module_name.uart_t()  # Constructs a new uart structure
# The rest is the same as above
```

In the first example, the text must contain preprocessed c code, while the second does it with the help of ``gcc`` compiler, available in path.

### Parsing ELF files

Module `c_tools.parser.elf` introduces some classes which support DWARF section parsing.

See `c_tools.io_param` module for usage examples.

### Deriving `io_param_t` structures

Execute `python -m c_tools.specializations.io_param --help` for usage instructions and additionally explore the module for in-depth information.

### Deriving XML files for MAT usage

Execute `python -m c_tools.specializations.mat --help` for usage instructions and additionally explore the module for in-depth information.
