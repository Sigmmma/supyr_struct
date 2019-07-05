# ####################################################
# ----      Supyr Struct exception classes      ---- #
# ####################################################


class SupyrStructError(Exception):
    pass


class IntegrityError(SupyrStructError):
    pass


class SanitizationError(SupyrStructError):
    pass


class DescEditError(SupyrStructError):
    pass


class DescKeyError(SupyrStructError):
    pass


class BinsizeError(SupyrStructError):
    pass


class FieldParseError(SupyrStructError):
    def __init__(self, *args, **kwargs):
        self.error_data = []  # used for storing extra data pertaining to the
        #                       exception so it can be more easily debugged.


class FieldSerializeError(SupyrStructError):
    def __init__(self, *args, **kwargs):
        self.error_data = []  # used for storing extra data pertaining to the
        #                       exception so it can be more easily debugged.
