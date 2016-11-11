'''
This module contains a class designed to pick the correct widget
to build to represent a field when given a descriptor.
'''
from .widgets import *
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
    _widget_map = None
    
    def __init__(self, *args, **kwargs):
        self._widget_map = dict(kwargs.get('widget_map', {}))

    def get_widget(self, desc):
        '''Returns the appropriate widget to use for the given descriptor.'''
        assert isinstance(desc, dict) is not None

        field_type = desc.get(TYPE)
        widget = desc.get(WIDGET)
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

        raise KeyError("Could not locate widget for %s" %field_type)

    def add_widget(self, field_type, widget):
        assert isinstance(field_type, FieldType)
        self._widget_map[id(field_type.big)] = widget
        self._widget_map[id(field_type.little)] = widget

# a default WidgetPicker to use if none is available
def_widget_picker = WidgetPicker()


# Time to populate the global widget_map with the default widgets!
