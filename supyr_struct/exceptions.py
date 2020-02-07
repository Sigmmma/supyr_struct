'''
This module holds all the exception classes shared by supyr.
'''

__all__ = (
    "SupyrStructError", "IntegrityError", "SanitizationError",
    "DescEditError", "DescKeyError", "BinsizeError",
    "FieldParseSerializeError", "FieldParseError", "FieldSerializeError"
    )

from supyr_struct.defs.constants import NAME, UNNAMED

# ####################################################
# ----      Supyr Struct exception classes      ---- #
# ####################################################

# TODO: These exceptions need short and sound explanations.

class SupyrStructError(Exception):
    '''
    Base supyr_struct exception class.
    '''


class IntegrityError(SupyrStructError):
    pass


class SanitizationError(SupyrStructError):
    # TODO: Short snippet explaining sanitization.
    '''
    Something went wrong during sanitization.
    '''


class DescEditError(SupyrStructError):
    pass


class DescKeyError(SupyrStructError):
    pass


class BinsizeError(SupyrStructError):
    pass


class FieldParseSerializeError(SupyrStructError):
    stack_error_data = ()  # used for storing extra data pertaining to the
    #                        exception so it can be more easily debugged.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stack_error_data = {}

    def add_stack_layer(self, **kwargs):
        desc = kwargs.get('desc', {})
        layer_id = (
            id(kwargs.get('parent')),
            id(kwargs.get('field_type', desc.get('TYPE'))),
            kwargs.get('attr_index')
            )

        if layer_id not in self.stack_error_data:
            self.stack_error_data[layer_id] = kwargs
            self.args = tuple(self.args) + (self._format_error_str(layer_id), )

    def _format_error_str(self, layer_id):
        error_data = self.stack_error_data[layer_id]
        desc = error_data.get('desc', {})
        field_type = error_data.get('field_type', desc.get('TYPE'))
        attr_index = error_data.get('attr_index')
        offset = error_data.get('offset', 0)
        root_offset = error_data.get('root_offset', 0)

        try:
            name = desc.get(NAME, UNNAMED)
        except Exception:
            name = UNNAMED

        return "    %s, index:%s, offset:%s, field_type:%s" % (
            name, attr_index, offset + root_offset, field_type)

    def __str__(self):
        return "\n".join(str(val) for val in (
            ("", ) + tuple(self.args[::-1])))


class FieldParseError(FieldParseSerializeError):
    pass


class FieldSerializeError(FieldParseSerializeError):
    pass
