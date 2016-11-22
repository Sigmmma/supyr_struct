from . import field_widgets
from . import widget_picker

__all__ = (
    )

# give the field_widgets module a reference to the widget_picker module
field_widgets.widget_picker = widget_picker
