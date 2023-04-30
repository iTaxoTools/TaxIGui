# -----------------------------------------------------------------------------
# TaxiGui - GUI for Taxi2
# Copyright (C) 2022-2023  Patmanidis Stefanos
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------------

"""GUI entry point"""


def run():
    """
    Show the Taxi2 window and enter the main event loop.
    Imports are done locally to optimize multiprocessing.
    """

    from . import config
    from .app import Application, skin
    from .main import Main

    app = Application()
    app.set_config(config)
    app.set_skin(skin)

    main = Main()
    main.show()

    app.exec()
