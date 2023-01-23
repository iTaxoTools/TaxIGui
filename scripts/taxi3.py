#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Launch the Taxi3 GUI"""

import multiprocessing
import matplotlib

from itaxotools.taxi3_gui import run


if __name__ == '__main__':
    multiprocessing.freeze_support()
    matplotlib.use('svg')
    matplotlib.use('pdf')
    run()
