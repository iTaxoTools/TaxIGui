# -----------------------------------------------------------------------------
# TaxiGui - GUI for Taxi2
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


class TypeMeta(type):
    _inheritors = dict()

    def __new__(cls, name, bases, attrs):
        obj = super().__new__(cls, name, bases, attrs)
        return cls._patch_object(obj, name, bases)

    @classmethod
    def _patch_object(cls, obj, name, bases):
        cls._inheritors[obj] = dict()
        obj._parent = None
        for base in bases:
            if issubclass(base, Type):
                cls._inheritors[base][name] = obj
                obj._parent = base
        return obj

    def __dir__(self):
        return super().__dir__() + list(self._inheritors[self].keys())

    def __getattr__(self, attr):
        if attr in self._inheritors[self]:
            return self._inheritors[self][attr]
        raise AttributeError(f'Type {repr(self.__name__)} has no subtype {repr(attr)}')

    def __iter__(self):
        return iter(self._inheritors[self].values())


class Type(metaclass=TypeMeta):
    """All subclasses are added as class attributes"""

    def __repr__(self):
        if self._parent:
            return f'<{".".join(self._get_name_chain())}>'
        return super().__repr__()

    def __eq__(self, other):
        return type(self) is type(other)

    @classmethod
    def _get_name_chain(cls):
        chain = [cls.__name__]
        while cls._parent:
            cls = cls._parent
            chain.append(cls.__name__)
        return reversed(chain[:-1])

    @property
    def type(self):
        return type(self)
