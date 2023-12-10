# TaxIGui

[![PyPI - Version](https://img.shields.io/pypi/v/itaxotools-taxi-gui)](
    https://pypi.org/project/itaxotools-taxi-gui)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/itaxotools-taxi-gui)](
    https://pypi.org/project/itaxotools-taxi-gui)
[![PyPI - License](https://img.shields.io/pypi/l/itaxotools-taxi-gui)](
    https://pypi.org/project/itaxotools-taxi-gui)
[![GitHub - Tests](https://img.shields.io/github/actions/workflow/status/iTaxoTools/TaxIGui/test.yml?label=tests)](
    https://github.com/iTaxoTools/TaxIGui/actions/workflows/test.yml)
[![GitHub - Windows](https://img.shields.io/github/actions/workflow/status/iTaxoTools/TaxIGui/windows.yml?label=windows)](
    https://github.com/iTaxoTools/TaxIGui/actions/workflows/windows.yml)

Calculation and analysis of pairwise sequence distances:

- **Versus All**: Calculate genetic distances among individuals and species
- **Versus Reference**: Find the best matches in a reference sequence database
- **Decontaminate**: Filter mismatches by comparing against two reference sequence databases
- **Dereplicate**: Remove sequences very similar to others from a dataset

This is a Qt GUI for [TaxI2](https://github.com/iTaxoTools/TaxI2).

![Screenshot](images/screenshot.png)

## Executables

[![Windows](https://img.shields.io/badge/Windows-blue.svg?style=for-the-badge&logo=windows)](
    https://github.com/iTaxoTools/TaxIGui/releases/latest)
[![MacOS](https://img.shields.io/badge/macOS-gray.svg?style=for-the-badge&logo=apple)](
    https://github.com/iTaxoTools/TaxIGui/releases/latest)

Download and run the standalone executables without installing Python.</br>
[See the latest release here.](https://github.com/iTaxoTools/TaxIGui/releases/latest)

## Installation

TaxIGui is available on PyPI. You can install it through `pip`:

```
pip install itaxotools-taxi-gui
```

## Usage

To launch the GUI, please use:
```
taxi-gui
```

Then select one of the available modes and follow the instructions on the screen.
