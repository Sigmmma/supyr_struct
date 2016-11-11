'''
This module contains a class designed to pick the correct widget
to build to represent a field when given a descriptor.
'''
from .widgets import *
from supyr_struct.field_types import *

# Maps the ids of each FieldType to a widget that can display it.
_widget_map = {}

def add_widget(field_type, widget):
    assert isinstance(field_type, FieldType)
    _widget_map[id(field_type.big)] = widget
    _widget_map[id(field_type.little)] = widget


class WidgetPicker():
    widget_map = None
    
    def __init__(self, *args, **kwargs):
        self.widget_map = dict(kwargs.get('widget_map', {}))

    def get_widget(self, desc):
        '''Returns the appropriate widget to use for the given descriptor.'''
        field_type = desc.get('TYPE')
        assert field_type is not None

        f_id = id(field_type)
        if f_id in self.widget_map:
            return self.widget_map[f_id]
        elif f_id in _widget_map:
            return _widget_map[f_id]

        raise KeyError("Could not locate widget for %s" %field_type)

    def add_widget(self, field_type, widget):
        assert isinstance(field_type, FieldType)
        self.widget_map[id(field_type.big)] = widget
        self.widget_map[id(field_type.little)] = widget

