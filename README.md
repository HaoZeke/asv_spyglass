# About [![Documentation](https://img.shields.io/badge/Documentation-latest-brightgreen?style=for-the-badge)](https://asv.readthedocs.io/projects/asv-spyglass/en/latest/)

`asv` output file comparer, for comparing across different environments or runs.

For other functionality, refer to the `asv` package or consider writing an
extension.

# Contributions

All contributions are welcome, this includes code and documentation
contributions but also questions or other clarifications. Note that we expect
all contributors to follow our [Code of
Conduct](https://github.com/airspeed-velocity/asv_spyglass/blob/main/CODE_OF_CONDUCT.md).

## Developing locally

A `pre-commit` job is setup on CI to enforce consistent styles, so it is best to
set it up locally as well (using [pipx](https://pypa.github.io/pipx/) for isolation):

```sh
# Run before commiting
pipx run pre-commit run --all-files
# Or install the git hook to enforce this
pipx run pre-commit install
```
