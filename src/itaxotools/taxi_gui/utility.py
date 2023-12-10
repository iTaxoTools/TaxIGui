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


def type_convert(value, type, default):
    try:
        return type(value)
    except ValueError:
        return default


def human_readable_size(size):
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1000.0 or unit == "GB":
            break
        size /= 1000.0
    if unit == "B":
        return f"{int(size)} {unit}"
    return f"{size:.2f} {unit}"


def human_readable_seconds(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)

    segments = [
        f'{int(h)} hour{"s" if h >= 2 else ""}' if h else None,
        f'{int(m)} minute{"s" if m >= 2 else ""}' if m else None,
        f"{s:.2f} seconds" if s else None,
    ]
    segments = (x for x in segments if x)
    return ", ".join(segments)
