# Repository Guidelines

## Project Structure & Module Organization
This repository is a small Python CLI tool for offline photo organization.

- [`organize_photos.py`](/home/cyberic/Projects/07-image-management/image-manager/organize_photos.py): main entrypoint and core logic for scanning, EXIF GPS extraction, province resolution, and file copying.
- [`china_province_bounds.json`](/home/cyberic/Projects/07-image-management/image-manager/china_province_bounds.json): offline province boundary data used for location mapping.
- [`tests/test_organize_photos.py`](/home/cyberic/Projects/07-image-management/image-manager/tests/test_organize_photos.py): regression tests for CLI behavior and core helpers.
- [`output/`](/home/cyberic/Projects/07-image-management/image-manager/output): generated runtime output; ignored by git.

Keep new code in the existing script unless the file becomes hard to navigate; split only when a clear module boundary appears.

## Build, Test, and Development Commands
- Run all commands inside the `conda` environment `misc`: `conda activate misc`
- `python3 organize_photos.py /path/to/photos`: preview classification without copying files.
- `python3 organize_photos.py /path/to/photos --apply`: execute the copy operation.
- `python3 organize_photos.py /path/to/photos --apply --output /tmp/out`: copy into a custom destination.
- `python3 -m unittest discover -s tests -v`: run the full test suite.

There is no separate build step. Development is local Python execution plus unit tests.

## Coding Style & Naming Conventions
Use Python 3.12+ with 4-space indentation and standard library-first solutions where practical. Prefer clear, small functions with explicit names such as `extract_gps` or `resolve_province`.

- `snake_case` for functions, variables, and test methods
- `UPPER_CASE` for constants
- Short doc-free code is preferred; add comments only when behavior is non-obvious

No formatter or linter is configured yet, so match the existing style manually.

## Testing Guidelines
Tests use the standard library `unittest` framework. Add or update tests for any change to CLI behavior, file-copy rules, GPS parsing, or province resolution.

Name test files as `test_*.py` and test methods as `test_<behavior>`. Favor temporary directories and mocks over real photo assets.

## Commit & Pull Request Guidelines
Current history uses short imperative commit messages, for example:

- `Add offline photo organizer script`
- `Add project README`

Follow that pattern: start with a verb, keep the subject concise, and describe one logical change per commit. Pull requests should include a brief summary, test results, and any behavior changes to CLI flags or output structure.

## Security & Data Safety
Do not change the default safety model lightly. This tool is designed to copy files, not move or delete them. Treat anything that could overwrite user photos as high risk and cover it with tests first.

## Environment Notes
Use the `misc` conda environment for local development, testing, and one-off runs. If dependencies are missing, install them with `pip install -r requirements.txt` after activating `misc`.
