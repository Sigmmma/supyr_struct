from supyr_struct.defs.constants import *
from supyr_struct.defs.block_def import BlockDef
from supyr_struct.fields import *

__all__ = ['sanitize_test', 'pass_fail']

pass_fail = {'fail': 0, 'pass': 0, 'test_count': 15}


def _print_error_test_fail(test_name):
    print("Failed '%s' sanitizing test." % test_name)


def _print_error_test_pass(test_name):
    print("Passed '%s' sanitizing test." % test_name)


def sanitize_test():
    # definitions to _test sanitize error catching and reporting routines
    _test = None

    try:  # endianness characters must be one of '<', '>', ''
        _test = BlockDef(NAME='_test', ENDIAN=None)
        _print_error_test_fail('endian_test')
        pass_fail['fail'] += 1
    except SanitizationError:
        _print_error_test_pass('endian_test')
        pass_fail['pass'] += 1

    try:  # cant have non-struct bit_based data outside a bitstruct
        _test = BlockDef(Bit('bit'), NAME='_test')
        _print_error_test_fail('bit_based_test1')
        pass_fail['fail'] += 1
    except SanitizationError:
        _print_error_test_pass('bit_based_test1')
        pass_fail['pass'] += 1

    try:  # bitstructs cant contain non-bit_based data
        _test = BlockDef(BitStruct('bitstruct', UInt8('int8')), NAME='_test')
        _print_error_test_fail('bit_based_test2')
        pass_fail['fail'] += 1
    except SanitizationError:
        _print_error_test_pass('bit_based_test2')
        pass_fail['pass'] += 1

    try:  # bitstructs cannot contain bitstructs
        _test = BlockDef(
            BitStruct('bitstruct_outer', BitStruct('bitstruct_inner')),
            NAME='_test'
            )
        _print_error_test_fail('bit_based_test3')
        pass_fail['fail'] += 1
    except SanitizationError:
        _print_error_test_pass('bit_based_test3')
        pass_fail['pass'] += 1

    try:  # values supplied as bytes to be decoded must be the right length
        _test = BlockDef(UInt32('int32', DEFAULT=b''), NAME='_test')
        _print_error_test_fail('decode_test')
        pass_fail['fail'] += 1
    except SanitizationError:
        _print_error_test_pass('decode_test')
        pass_fail['pass'] += 1

    try:  # cannot use oe_size fields inside a struct
        _test = BlockDef(
            Struct('struct',
                StreamAdapter('stream', DECODER=lambda: 0,
                    SUB_STRUCT=Struct('s'))
                ),
            NAME='_test'
            )
        _print_error_test_fail('oe_size_test')
        pass_fail['fail'] += 1
    except SanitizationError:
        _print_error_test_pass('oe_size_test')
        pass_fail['pass'] += 1

    try:  # cannot use containers inside structs
        _test = BlockDef(Struct('struct', Array('array')), NAME='_test')
        _print_error_test_fail('container_inside_struct_test')
        pass_fail['fail'] += 1
    except SanitizationError:
        _print_error_test_pass('container_inside_struct_test')
        pass_fail['pass'] += 1

    try:  # variable size data must have its size defined
        _test = BlockDef(BytesRaw('data'), NAME='_test')
        _print_error_test_fail('var_size_test1')
        pass_fail['fail'] += 1
    except SanitizationError:
        _print_error_test_pass('var_size_test1')
        pass_fail['pass'] += 1

    try:  # var_size data in a struct must have its size statically defined
        _test = BlockDef(
            Struct('struct', BytesRaw('data', SIZE=None)),
            NAME='_test'
            )
        _print_error_test_fail('var_size_test2')
        pass_fail['fail'] += 1
    except SanitizationError:
        _print_error_test_pass('var_size_test2')
        pass_fail['pass'] += 1

    try:  # non-open ended arrays must have a defined size
        _test = BlockDef(Array('array', SUB_STRUCT=None), NAME='_test')
        _print_error_test_fail('array_test1')
        pass_fail['fail'] += 1
    except SanitizationError:
        _print_error_test_pass('array_test1')
        pass_fail['pass'] += 1

    try:  # arrays must have a SUB_STRUCT entry
        _test = BlockDef(Array('array', SIZE=0), NAME='_test')
        _print_error_test_fail('array_test2')
        pass_fail['fail'] += 1
    except SanitizationError:
        _print_error_test_pass('array_test2')
        pass_fail['pass'] += 1

    try:  # all Fields must be given names
        _test = BlockDef({TYPE: UInt8}, NAME='_test')
        _print_error_test_fail('name_test1')
        pass_fail['fail'] += 1
    except SanitizationError:
        _print_error_test_pass('name_test1')
        pass_fail['pass'] += 1

    try:  # all names must be strings(dur)
        _test = BlockDef({TYPE: UInt8, NAME: None}, NAME='_test')
        _print_error_test_fail('name_test2')
        pass_fail['fail'] += 1
    except SanitizationError:
        _print_error_test_pass('name_test2')
        pass_fail['pass'] += 1

    try:  # names cannot be descriptor keywords
        _test = BlockDef(NAME=NAME)
        _print_error_test_fail('name_test3')
        pass_fail['fail'] += 1
    except SanitizationError:
        _print_error_test_pass('name_test3')
        pass_fail['pass'] += 1

    try:  # names cannot be descriptor keywords
        _test = BlockDef(NAME='')
        _print_error_test_fail('name_test4')
        pass_fail['fail'] += 1
    except SanitizationError:
        _print_error_test_pass('name_test4')
        pass_fail['pass'] += 1

# run some tests
if __name__ == '__main__':
    pass_fail['fail'] = pass_fail['pass'] = 0
    sanitize_test()
    print('%s passed, %s failed. %s tests total.' % (pass_fail['pass'],
                                                     pass_fail['fail'],
                                                     pass_fail['test_count']))
    input()
