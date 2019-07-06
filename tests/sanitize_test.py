#from supyr_struct.util import *
from supyr_struct.exceptions import SanitizationError
from supyr_struct.defs.block_def import BlockDef
from supyr_struct.field_types import Struct, Array, BitStruct, UInt8, Bit,\
     StreamAdapter, BytesRaw
from supyr_struct.defs.constants import TYPE, NAME

__all__ = ['sanitize_test', 'pass_fail']

pass_fail = {'fail': 0, 'pass': 0, 'test_count': 0}


def _error_test_fail(test_name):
    print("Failed '%s' sanitizing test." % test_name)
    pass_fail['fail'] += 1
    pass_fail['test_count'] += 1


def _error_test_pass(test_name):
    print("Passed '%s' sanitizing test." % test_name)
    pass_fail['pass'] += 1
    pass_fail['test_count'] += 1


def sanitize_test():
    # definitions to _test sanitize error catching and reporting routines

    try:  # endianness characters must be one of '<', '>', ''
        _test = BlockDef('test', ENDIAN=None)
        _error_test_fail('endian_test')
    except SanitizationError:
        _error_test_pass('endian_test')

    try:  # cant have non-struct bit_based data outside a bitstruct
        _test = BlockDef('test', Bit('bit'))
        _error_test_fail('bit_based_test1')
    except SanitizationError:
        _error_test_pass('bit_based_test1')

    try:  # bitstructs cant contain non-bit_based data
        _test = BlockDef('test', BitStruct('bitstruct', UInt8('int8')))
        _error_test_fail('bit_based_test2')
    except SanitizationError:
        _error_test_pass('bit_based_test2')

    try:  # bitstructs cannot contain bitstructs
        _test = BlockDef('test',
            BitStruct('bitstruct_outer', BitStruct('bitstruct_inner'))
            )
        _error_test_fail('bit_based_test3')
    except SanitizationError:
        _error_test_pass('bit_based_test3')

    try:  # cannot use oe_size fields inside a struct
        _test = BlockDef('test',
            Struct('struct',
                StreamAdapter('stream', DECODER=lambda: 0,
                    SUB_STRUCT=Struct('s'))
                )
            )
        _error_test_fail('oe_size_test')
    except SanitizationError:
        _error_test_pass('oe_size_test')

    try:  # cannot use containers inside structs
        _test = BlockDef('test', Struct('struct', Array('array')))
        _error_test_fail('container_inside_struct_test')
    except SanitizationError:
        _error_test_pass('container_inside_struct_test')

    try:  # variable size data must have its size defined
        _test = BlockDef('test', BytesRaw('data'))
        _error_test_fail('var_size_test1')
    except SanitizationError:
        _error_test_pass('var_size_test1')

    try:  # var_size data in a struct must have its size statically defined
        _test = BlockDef('test',
            Struct('struct', BytesRaw('data', SIZE=None))
            )
        _error_test_fail('var_size_test2')
    except SanitizationError:
        _error_test_pass('var_size_test2')

    try:  # non-open ended arrays must have a defined size
        _test = BlockDef('test', Array('array', SUB_STRUCT=None))
        _error_test_fail('array_test1')
    except SanitizationError:
        _error_test_pass('array_test1')

    try:  # arrays must have a SUB_STRUCT entry
        _test = BlockDef('test', Array('array', SIZE=0))
        _error_test_fail('array_test2')
    except SanitizationError:
        _error_test_pass('array_test2')

    try:  # all fields must be given names
        _test = BlockDef('test', {TYPE: UInt8})
        _error_test_fail('name_test1')
    except SanitizationError:
        _error_test_pass('name_test1')

    try:  # all names must be strings(dur)
        _test = BlockDef('test', {TYPE: UInt8, NAME: None})
        _error_test_fail('name_test2')
    except SanitizationError:
        _error_test_pass('name_test2')

    try:  # names cannot be descriptor keywords
        _test = BlockDef(NAME, UInt8('test'))
        _error_test_fail('name_test3')
    except SanitizationError:
        _error_test_pass('name_test3')

    try:  # names cannot be empty strings
        _test = BlockDef('', UInt8('test'))
        _error_test_fail('name_test4')
    except SanitizationError:
        _error_test_pass('name_test4')

# run some tests
if __name__ == '__main__':
    pass_fail['fail'] = pass_fail['pass'] = 0
    sanitize_test()
    print('%s passed, %s failed. %s%% passed.' % (
        pass_fail['pass'], pass_fail['fail'],
        str(pass_fail['pass'] * 100 / pass_fail['test_count']).split('.')[0]))
    input()
