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

from .resources import icons, pixmaps
from .tasks import decontaminate, dereplicate, versus_all, versus_reference

title = "TaxI2.2"
icon = icons.taxi2
pixmap = pixmaps.taxi2

dashboard = "legacy"
show_open = False
show_save = False

tasks = [
    versus_all,
    versus_reference,
    dereplicate,
    decontaminate,
]
