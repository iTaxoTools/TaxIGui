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

![Screenshot](https://raw.githubusercontent.com/iTaxoTools/TaxIGui/v0.2.5/images/screenshot.png)

## Executables

Download and run the standalone executables without installing Python.

[![Release](https://img.shields.io/badge/release-TaxI_2.2.2-red?style=for-the-badge)](
    https://github.com/iTaxoTools/TaxIGui/releases/v0.2.5)
[![Windows](https://img.shields.io/badge/Windows-blue.svg?style=for-the-badge&logo=data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPCEtLSBDcmVhdGVkIHdpdGggSW5rc2NhcGUgKGh0dHA6Ly93d3cuaW5rc2NhcGUub3JnLykgLS0+Cjxzdmcgd2lkdGg9IjQ4IiBoZWlnaHQ9IjQ4IiB2ZXJzaW9uPSIxLjEiIHZpZXdCb3g9IjAgMCAxMi43IDEyLjciIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CiA8ZyBmaWxsPSIjZmZmIiBzdHJva2UtbGluZWNhcD0ic3F1YXJlIiBzdHJva2Utd2lkdGg9IjMuMTc0OSI+CiAgPHJlY3QgeD0iLjc5MzczIiB5PSIuNzkzNzMiIHdpZHRoPSI1LjAyNyIgaGVpZ2h0PSI1LjAyNyIvPgogIDxyZWN0IHg9IjcuMTQzNiIgeT0iLjc5MzczIiB3aWR0aD0iNC43NjI0IiBoZWlnaHQ9IjUuMDI3Ii8+CiAgPHJlY3QgeD0iLjc5MzczIiB5PSI2Ljg3OSIgd2lkdGg9IjUuMDI3IiBoZWlnaHQ9IjUuMDI3Ii8+CiAgPHJlY3QgeD0iNy4xNDM2IiB5PSI2Ljg3OSIgd2lkdGg9IjQuNzYyNCIgaGVpZ2h0PSI1LjAyNyIvPgogPC9nPgo8L3N2Zz4K)](
    https://github.com/iTaxoTools/TaxIGui/releases/download/v0.2.5/TaxI2.2.2-windows-x64.exe)
[![MacOS](https://img.shields.io/badge/macOS-slategray.svg?style=for-the-badge&logo=apple)](
    https://github.com/iTaxoTools/TaxIGui/releases/download/v0.2.5/TaxI2.2.2-macos-universal2.dmg)

## Installation

TaxIGui is available on PyPI and can be installed using `pip`:

```
pip install itaxotools-taxi-gui
```

After installation, run the program with:

```
taxi-gui
```
