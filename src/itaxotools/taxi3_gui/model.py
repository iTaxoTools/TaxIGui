# -----------------------------------------------------------------------------
# Taxi3Gui - GUI for Taxi3
# Copyright (C) 2022  Patmanidis Stefanos
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

from PySide6 import QtCore
# from PySide6 import QtWidgets
# from PySide6 import QtGui

# from pathlib import Path
from typing import Callable, Optional

# from itaxotools.common.widgets import VectorIcon
# from itaxotools.common.resources import get_common
# from itaxotools.common.utility import override


class Property():
    def __init__(self,
        type: type = object,
        fget: Optional[Callable] = None,
        fset: Optional[Callable] = None,
        notify: Optional[Callable] = None,
        constant: bool = False,
    ):
        self.type = type
        self.fget = fget
        self.fset = fset
        self.notify = notify
        self.constant = constant


class _ObjectMeta(type(QtCore.QObject)):
    def __new__(cls, name, bases, classdict):
        properties = {
            key: classdict[key] for key in classdict
            if isinstance(classdict[key], Property)}
        for key, property in properties.items():
            _key = f'_val_{key}'
            _get = f'_get_{key}'
            _set = f'_set_{key}'
            _notify = None
            if property.notify:
                _notify = [x for x in classdict if classdict[x] is property.notify][0]
            def getter(self):
                return getattr(self, _key)
            def setter(self, value):
                setattr(self, _key, value)
                if _notify:
                    getattr(self, _notify).emit(value)
            property.fget = property.fget or getter
            property.fset = property.fset or setter
            classdict[key] = QtCore.Property(
                type = property.type,
                fget = property.fget,
                fset = property.fset,
                notify = property.notify,
                constant = property.constant,
                )
        obj = super().__new__(cls, name, bases, classdict)
        return obj


class Object(QtCore.QObject, metaclass=_ObjectMeta):
    changed = QtCore.Signal(str)
    name = Property(str, notify=changed)

    def __init__(self, name):
        super().__init__()
        self.name = name


class Group(Object):
    pass


class Sequence(Object):
    pass


class Task(Object):
    pass
