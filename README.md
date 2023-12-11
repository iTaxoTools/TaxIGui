# TaxIGui

[![PyPI - Version](https://img.shields.io/pypi/v/itaxotools-taxi-gui?color=tomato)](
    https://pypi.org/project/itaxotools-taxi-gui)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/itaxotools-taxi-gui)](
    https://pypi.org/project/itaxotools-taxi-gui)
[![GitHub - Tests](https://img.shields.io/github/actions/workflow/status/iTaxoTools/TaxIGui/test.yml?label=tests)](
    https://github.com/iTaxoTools/TaxIGui/actions/workflows/test.yml)
[![GitHub - Windows](https://img.shields.io/github/actions/workflow/status/iTaxoTools/TaxIGui/windows.yml?label=windows)](
    https://github.com/iTaxoTools/TaxIGui/actions/workflows/windows.yml)
[![GitHub - macOS](https://img.shields.io/github/actions/workflow/status/iTaxoTools/TaxIGui/macos.yml?label=macos)](
    https://github.com/iTaxoTools/TaxIGui/actions/workflows/macos.yml)

Calculation and analysis of pairwise sequence distances:

- **Versus All**: Calculate genetic distances among individuals and species
- **Versus Reference**: Find the best matches in a reference sequence database
- **Decontaminate**: Filter mismatches by comparing against two reference sequence databases
- **Dereplicate**: Remove sequences very similar to others from a dataset

This is a Qt GUI for [TaxI2](https://github.com/iTaxoTools/TaxI2).

![Screenshot](https://raw.githubusercontent.com/iTaxoTools/TaxIGui/v0.2.2/images/screenshot.png)

## Executables

Download and run the standalone executables without installing Python.

[![Release](https://img.shields.io/badge/release-TaxI_2.2.0-red?style=for-the-badge)](
    https://github.com/iTaxoTools/TaxIGui/releases/v0.2.2)
[![Windows](https://img.shields.io/badge/Windows-blue.svg?style=for-the-badge&logo=windows)](
    https://github.com/iTaxoTools/TaxIGui/releases/download/v0.2.2/TaxI2.2.0-windows-x64.exe)
[![MacOS](https://img.shields.io/badge/macOS-slategray.svg?style=for-the-badge&logo=apple)](
    https://github.com/iTaxoTools/TaxIGui/releases/download/v0.2.2/TaxI2.2.0-macos-universal2.dmg)

## Installation

TaxIGui is available on PyPI. You can install it through `pip`:

```
pip install itaxotools-taxi-gui
```

Then launch the GUI and follow the instructions on the screen:
```
taxi-gui
```
