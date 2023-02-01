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

from PySide6 import QtCore

from enum import Enum
from dataclasses import dataclass
from typing import Callable, ClassVar, Optional, Union, NamedTuple, Type
from types import UnionType

from itaxotools.common.utility import AttrDict


class Instance:
    """Pass as type or instance to instantiate a property by default"""
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class _Instance:
    """Internal instructions for default class instatiation"""
    def __init__(self, type, *args, **kwargs):
        self.type = type
        self.args = args
        self.kwargs = kwargs


class Property:

    key_ref = 'properties'
    key_list = '_property_list'

    def __init__(self, type=object, default=None):
        if isinstance(type, UnionType):
            type = object
        self.type = type
        self.default = default

    @staticmethod
    def key_value(key):
        return f'_property_{key}_value'

    @staticmethod
    def key_notify(key):
        return f'_property_{key}_notify'

    @staticmethod
    def key_getter(key):
        return f'_property_{key}_getter'

    @staticmethod
    def key_setter(key):
        return f'_property_{key}_setter'

    @staticmethod
    def key_default(key):
        return f'_property_{key}_default'


class PropertyRef:
    def __init__(self, parent, key):
        self._parent = parent
        self._key = key

    @property
    def notify(self):
        return getattr(self._parent, Property.key_notify(self._key))

    @property
    def get(self):
        return getattr(self._parent, Property.key_getter(self._key))

    @property
    def set(self):
        return getattr(self._parent, Property.key_setter(self._key))

    @property
    def default(self):
        default = getattr(self._parent, Property.key_default(self._key))
        if isinstance(default, _Instance):
            return default.type(*default.args, **default.kwargs)
        return default

    @property
    def key(self):
        return self._key

    @property
    def value(self):
        return self.get()

    @value.setter
    def value(self, value):
        return self.set(value)

    def update(self):
        self.notify.emit(self.get())


class PropertiesRef:
    def __init__(self, parent):
        self._parent = parent

    def __getattr__(self, attr):
        if attr in self._list():
            return PropertyRef(self._parent, attr)
        raise AttributeError(f'{repr(type(self._parent).__name__)} has no property: {repr(attr)}')

    def __getitem__(self, key):
        return self.__getattr__(key)

    def __dir__(self):
        return super().__dir__() + self._list()

    def _list(self):
        return getattr(self._parent, Property.key_list)

    def __iter__(self):
        return (self[key] for key in self._list())


class PropertyMeta(type(QtCore.QObject)):
    def __new__(cls, name, bases, attrs):
        properties = {
            key: attrs[key] for key in attrs
            if isinstance(attrs[key], Property)}
        cls._init_list(bases, attrs)
        for key, prop in properties.items():
            cls._register_property(attrs, key, prop)
        cls._add_ref(attrs)
        obj = super().__new__(cls, name, bases, attrs)
        return obj

    def _init_list(bases, attrs):
        key_list = Property.key_list
        lists = [getattr(base, key_list, []) for base in bases]
        attrs[key_list] = sum(lists, [])

    def _register_property(attrs, key, prop):
        key_value = Property.key_value(key)
        key_notify = Property.key_notify(key)
        key_getter = Property.key_getter(key)
        key_setter = Property.key_setter(key)
        key_default = Property.key_default(key)
        key_list = Property.key_list

        notify = QtCore.Signal(prop.type)

        def getter(self):
            return getattr(self, key_value, None)

        def setter(self, value):
            old = getattr(self, key_value, None)
            setattr(self, key_value, value)
            if old != value:
                getattr(self, key_notify).emit(value)

        default = prop.default
        if default == Instance:
            default = _Instance(prop.type)
        if isinstance(default, Instance):
            default = _Instance(prop.type, *default.args, **default.kwargs)

        attrs[key_list].append(key)

        attrs[key_notify] = notify
        attrs[key_getter] = getter
        attrs[key_setter] = setter
        attrs[key_default] = default

        attrs[key] = QtCore.Property(
            type=prop.type,
            fget=getter,
            fset=setter,
            notify=notify,
        )

    def _add_ref(attrs):
        key_ref = Property.key_ref

        def getref(self):
            return PropertiesRef(self)

        attrs[key_ref] = property(getref)


class PropertyObject(QtCore.QObject, metaclass=PropertyMeta):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._set_property_defaults()

    def _set_property_defaults(self):
        for property in self.properties:
            property.set(property.default)

    def as_dict(self):
        return AttrDict({
            property.key: property.value
            for property in self.properties
        })


class EnumObjectMeta(PropertyMeta):
    def __new__(cls, name, bases, attrs):
        enum = attrs.get('enum', None)
        if not enum:
            return super().__new__(cls, name, bases, attrs)

        get_key = attrs.get('get_key', lambda x: x.key)
        get_type = attrs.get('get_type', lambda x: x.type)
        get_default = attrs.get('get_default', lambda x: x.default)
        for field in enum:
            attrs[get_key(field)] = Property(get_type(field), get_default(field))
        return super().__new__(cls, name, bases, attrs)


class EnumObject(PropertyObject, metaclass=EnumObjectMeta):
    enum: Enum

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'enum' in dir(self):
            self.reset()

    def reset(self):
        self._set_property_defaults()


@dataclass(frozen=True)
class Binding:
    bindings: ClassVar = dict()

    signal: QtCore.SignalInstance
    slot: Callable

    @classmethod
    def _bind(cls, signal, slot, proxy=None):
        if proxy:
            def proxy_slot(value):
                slot(proxy(value))
            bind_slot = proxy_slot
        else:
            bind_slot = slot
        signal.connect(bind_slot)
        id = cls(signal, slot)
        cls.bindings[id] = bind_slot
        return id

    @classmethod
    def _unbind(cls, signal, slot):
        id = cls(signal, slot)
        bind_slot = cls.bindings[id]
        signal.disconnect(bind_slot)
        return id


class Binder(set):

    def bind(
        self,
        source: Union[PropertyRef, QtCore.SignalInstance],
        destination: Union[PropertyRef, Callable],
        proxy: Optional[Callable] = None,
    ):

        if isinstance(source, PropertyRef):
            signal = source.notify
        else:
            signal = source

        if isinstance(destination, PropertyRef):
            slot = destination.set
        else:
            slot = destination

        key = Binding._bind(signal, slot, proxy)
        if isinstance(source, PropertyRef):
            source.update()

        self.add(key)

    def unbind(
        self,
        source: Union[PropertyRef, QtCore.SignalInstance],
        destination: Union[PropertyRef, Callable],
        remove=True,
    ):

        if isinstance(source, PropertyRef):
            signal = source.notify
        else:
            signal = source

        if isinstance(destination, PropertyRef):
            slot = destination.set
        else:
            slot = destination

        key = Binding._unbind(signal, slot)
        if remove:
            self.remove(key)
        return key

    def unbind_all(self):
        for key in self:
            self.unbind(key.signal, key.slot, remove=False)
        self.clear()


class Guard:
    def __init__(self):
        self.locked = False

    def __enter__(self):
        self.locked = True

    def __exit__(self, type, value, trace):
        self.locked = False

    def __bool__(self):
        return self.locked


def type_convert(value, type, default):
    try:
        return type(value)
    except ValueError:
        return default


def human_readable_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1000.0 or unit == 'GB':
            break
        size /= 1000.0
    return f'{size:.2f} {unit}'


def human_readable_seconds(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)

    segments = [
        f'{int(h)} hour{"s" if h >= 2 else ""}' if h else None,
        f'{int(m)} minute{"s" if m >= 2 else ""}' if m else None,
        f'{s:.2f} seconds' if s else None,
    ]
    segments = (x for x in segments if x)
    return ', '.join(segments)
