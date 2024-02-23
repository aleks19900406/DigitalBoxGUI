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

For use cases, see the actual implementations:
* byte stream → `stream.byte.SerialStream` and `stream.byte.TCPStream`
* list stream → `stream.coder.CoderStream`
* chaining stream → `stream.packer.PackerStream`
* synchronous stream → `stream.specializations.hisense.HisenseStream`