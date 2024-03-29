#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Launch the Taxi2 GUI"""

import multiprocessing

from itaxotools.taxi_gui import run

if __name__ == "__main__":
    multiprocessing.freeze_support()
    run()
