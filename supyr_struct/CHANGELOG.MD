# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
 - Michelle is now in [LICENSE.TXT](LICENSE.TXT).
 - This changelog!
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
 - util.sanitize_path in favor of path_normalize.
