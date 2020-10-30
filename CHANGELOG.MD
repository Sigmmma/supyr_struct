# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.5.4]
### Changed
 - Update build config for Python 3.9.

## [1.5.3]
### Changed
 - Fix incorrect feeding of data in split path

## [1.5.2]
### Changed
 - Fix readme potentially breaking setup.

## [1.5.1]
### Added
 - Many pieces of documentation.
 - util.reversed_enumerate because you can't do reversed(enumerate(iterable))

### Changed
 - Lots of cleaning up in how things are internally implemented.

## [1.5.0]
### Changed
 - Change endianness forcing implementation to remove a layer of indirection in parser, serializer, encoder, and decoder.
 - Fix some broken binary files in the project.
 - Improve readability of parse/serialize error stack trace.
 - Made parser_func, serializer_func, decoder_func, encoder_func, and sizecalc_func proper instance methods in FieldType.
 - parser, serializer, decoder, encoder, and sizecalc_funcs are now in their own submodules.
 - Slight speedup all around.

## [1.4.1] Meta update
### Changed
 - Add a bunch of useful metadata to setup.py
 - Better .gitignore.
 - .gitattributes now enforces LF line endings for operating system agnostic files.
 - Project structure got updated to make it easier for people to install the package from the repository.
 - Readme updated for PyPI.

## [1.4.0]
### Added
 - Michelle is now in [LICENSE.TXT](LICENSE.TXT).
 - This changelog!
 - util is now fully documented! (More to come.)
 - util.path_normalize for normalizing paths and easing string comparisons.
 - util.path_replace.
 - util.path_split.
 - util.tagpath_to_fullpath for handling directory relative paths case insensitively on case sensitive filesystems.

### Changed
 - Add prints to a few try-except blocks
 - Fix [LICENSE.TXT](LICENSE.TXT) for 80 character wide terminals
 - Fix a few try-except pairs that were catching keyboard interrupts
 - Fix exception when trying to serialize a block without a filepath
 - Port [README](README.MD) to MarkDown
 - Simplified and sped up util.str_to_identifier
 - Tag.filepath instance variable now returns and converts to a pathlib Path object
 - util.is_in_dir is now posix compatible (Respects symlinks and works on case sensitive file systems)

### Removed
 - util.PATHDIV constant in favor of letting pathlib handle that.
 - util.fcc and util.fourcc macros. Use util.fourcc_to_int and util.int_to_fourcc instead.
 - util.sanitize_path in favor of util.path_normalize.
 - **REMOVED SUPPORT FOR VERSIONS OF PYTHON BELOW 3.5**
