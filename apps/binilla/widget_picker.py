'''
This module contains a class designed to pick the correct widget
to build to represent a field when given a descriptor.
'''
from . import constants as const
from .field_widgets import *
from supyr_struct.field_types import *

__all__ = ("add_widget", "def_widget_picker", "WidgetPicker")

# Maps the ids of each FieldType to a widget that can display it.
_widget_map = {}

def add_widget(field_type, widget):
    '''
    Adds the given widget to the global widget_map
    using the id of the given FieldType as the key.
    '''
    assert isinstance(field_type, FieldType)
    _widget_map[id(field_type.big)] = widget
    _widget_map[id(field_type.little)] = widget


class WidgetPicker():
    '''
    This class is a simple widget class manager which stores
    an internal mapping of widgets indexed by the id of the
    FieldType instance they are representing.
    '''
    _widget_map = None  # a map of FieldType instance ids to widgets
    return_null_widget = True  # whether or not to return the NullWidget when
    #                            a widget cant be found for the given field
    null_widget = NullCanvas  # the widget used to represent unknown fields

    def __init__(self, *args, **kwargs):
        self._widget_map = dict(kwargs.get('widget_map', {}))

    def get_widget(self, desc):
        '''Returns the appropriate widget to use for the given descriptor.'''
        assert isinstance(desc, dict) is not None

        field_type = desc.get(const.TYPE)
        widget = desc.get(const.WIDGET)
        assert field_type is not None

        f_id = id(field_type)
        if widget is not None:
            # return the descriptor defined widget
            return widget
        elif f_id in self._widget_map:
            # return the widget defined in the internal widget_map
            return self._widget_map[f_id]
        elif f_id in _widget_map:
            # return the widget defined in the global widget_map
            return _widget_map[f_id]
        elif self.return_null_widget:
            return self.null_widget

        raise KeyError("Could not locate widget for %s" %field_type)

    def add_widget(self, field_type, widget):
        assert isinstance(field_type, FieldType)
        self._widget_map[id(field_type.big)] = widget
        self._widget_map[id(field_type.little)] = widget

# a default WidgetPicker to use if none is available
def_widget_picker = WidgetPicker()


# Time to populate the global widget_map with the default widgets!
XXXX = None  # PLACEHOLDER STUFF
add_widget(Union, XXXX)
add_widget(Switch, XXXX)
add_widget(StreamAdapter, XXXX)

for f_type in (Void, Pad):
    add_widget(f_type, XXXX)

for f_type in (Array, WhileArray):
    add_widget(f_type, XXXX)
    
for f_type in (Container, Struct, QStruct, BitStruct):
    add_widget(f_type, XXXX)

for f_type in (BitUInt, BitSInt, Bit1SInt, BigUInt, BigSInt, Big1SInt,
               Bit, UInt8, SInt8, Pointer32, Pointer64, UDecimal, SDecimal,
               UInt16, UInt24, UInt32, UInt64, Float,
               SInt16, SInt24, SInt32, SInt64, Double):
    add_widget(f_type, XXXX)

for f_type in (TimestampFloat, Timestamp):
    add_widget(f_type, XXXX)

for f_type in (BitUEnum, BitSEnum, BitBool, BigUEnum, BigSEnum, BigBool,
               UEnum8,  SEnum8, UEnum16, UEnum24, UEnum32, UEnum64,
               SEnum16, SEnum24, SEnum32, SEnum64):
    add_widget(f_type, XXXX)

for f_type in (Bool8, Bool16, Bool24, Bool32, Bool64):
    add_widget(f_type, XXXX)

for f_type in (BytesRaw, BytearrayRaw, BytesRawEnum):
    add_widget(f_type, XXXX)

for f_type in (UInt8Array, SInt8Array, UInt16Array, SInt16Array, UInt32Array,
               SInt32Array, UInt64Array, SInt64Array, FloatArray, DoubleArray):
    add_widget(f_type, XXXX)

for f_type in (tuple(str_field_types.values()) +
               tuple(str_raw_field_types.values()) +
               tuple(cstr_field_types.values()) +
               (StrUtf16, StrUtf32, CStrUtf16, CStrUtf32, StrRawUtf16,
                StrRawUtf32, StrUtf8, CStrUtf8, StrLatin1, CStrLatin1,
                StrRawLatin1, StrAscii, CStrAscii, StrRawAscii, StrRawUtf8)):
    add_widget(f_type, XXXX)

add_widget(StrHex, XXXX)
