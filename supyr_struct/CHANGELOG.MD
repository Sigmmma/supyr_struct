# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
 - Michelle is now in [LICENSE.TXT](LICENSE.TXT).
 - This changelog!
 - [util](util.py).path_normalize for normalizing paths and easing string comparisons.
 - [util](util.py).path_replace.
 - [util](util.py).path_split.
 - [util](util.py).tagpath_to_fullpath for handling directory relative paths case insensitively on case sensitive filesystems.

### Changed
 - Add prints to a few try-except blocks
 - Fix [LICENSE.TXT](LICENSE.TXT) for 80 character wide terminals
 - Fix a few try-except pairs that were catching keyboard interrupts
 - Fix exception when trying to serialize a block without a filepath
 - Port [README](README.MD) to MarkDown
 - Simplified and sped up [util](util.py).str_to_identifier
 - [Tag](tag.py).filepath instance variable now returns and converts to a pathlib Path object
 - [util](util.py).is_in_dir is now posix compatible (Respects symlinks and works on case sensitive file systems)

### Removed
 - [util](util.py).PATHDIV constant in favor of letting pathlib handle that.
 - [util](util.py).fcc and util.fourcc macros. Use fourcc_to_int and int_to_fourcc instead.
 - [util](util.py).sanitize_path in favor of path_normalize.
