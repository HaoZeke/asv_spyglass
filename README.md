# About [![Documentation](https://img.shields.io/badge/Documentation-latest-brightgreen?style=for-the-badge)](https://asv.readthedocs.io/projects/asv-spyglass/en/latest/)

`asv` output file comparer, for comparing across different environments or runs.

For other functionality, refer to the `asv` package or consider writing an
extension.

## Basic usage

### Comparing two benchmarks

This is agnostic to the environment, however the `benchmarks.json` is required.
The practical usage of this command is to compare `asv` runs from builds which
are not handled by the `asv` environment management machinery.

``` sh
➜ asv-spyglass compare tests/data/d6b286b8-virtualenv-py3.12-numpy.json tests/data/d6b286b8-rattler-py3.12-numpy.json tests/data/d6b286b8_asv_samples_benchmarks.json


| Change   | Before      | After       |   Ratio | Benchmark (Parameter)                                                                                                               |
|----------|-------------|-------------|---------|-------------------------------------------------------------------------------------------------------------------------------------|
| -        | 157±3ns     | 137±3ns     |    0.87 | benchmarks.TimeSuiteDecoratorSingle.time_keys(10) [rgx1gen11/virtualenv-py3.12-numpy -> rgx1gen11/rattler-py3.12-numpy]             |
| -        | 643±2ns     | 543±2ns     |    0.84 | benchmarks.TimeSuiteDecoratorSingle.time_keys(100) [rgx1gen11/virtualenv-py3.12-numpy -> rgx1gen11/rattler-py3.12-numpy]            |
|          | 1.17±0μs    | 1.07±0μs    |    0.91 | benchmarks.TimeSuiteDecoratorSingle.time_keys(200) [rgx1gen11/virtualenv-py3.12-numpy -> rgx1gen11/rattler-py3.12-numpy]            |
| +        | 167±3ns     | 187±3ns     |    1.12 | benchmarks.TimeSuiteDecoratorSingle.time_values(10) [rgx1gen11/virtualenv-py3.12-numpy -> rgx1gen11/rattler-py3.12-numpy]           |
| +        | 685±4ns     | 785±4ns     |    1.15 | benchmarks.TimeSuiteDecoratorSingle.time_values(100) [rgx1gen11/virtualenv-py3.12-numpy -> rgx1gen11/rattler-py3.12-numpy]          |
| +        | 1.26±0μs    | 1.46±0μs    |    1.16 | benchmarks.TimeSuiteDecoratorSingle.time_values(200) [rgx1gen11/virtualenv-py3.12-numpy -> rgx1gen11/rattler-py3.12-numpy]          |
| +        | 1.17±0.01μs | 1.37±0.01μs |    1.17 | benchmarks.TimeSuiteMultiDecorator.time_ranges(10, 'arange') [rgx1gen11/virtualenv-py3.12-numpy -> rgx1gen11/rattler-py3.12-numpy]  |
|          | 211±0.9ns   | 231±0.9ns   |    1.09 | benchmarks.TimeSuiteMultiDecorator.time_ranges(10, 'range') [rgx1gen11/virtualenv-py3.12-numpy -> rgx1gen11/rattler-py3.12-numpy]   |
| +        | 3.43±0.02μs | 3.83±0.02μs |    1.12 | benchmarks.TimeSuiteMultiDecorator.time_ranges(100, 'arange') [rgx1gen11/virtualenv-py3.12-numpy -> rgx1gen11/rattler-py3.12-numpy] |
| +        | 551±1ns     | 651±1ns     |    1.18 | benchmarks.TimeSuiteMultiDecorator.time_ranges(100, 'range') [rgx1gen11/virtualenv-py3.12-numpy -> rgx1gen11/rattler-py3.12-numpy]  |
|          | 1.14±0μs    | 1.04±0μs    |    0.91 | benchmarks.time_ranges_multi(10, 'arange') [rgx1gen11/virtualenv-py3.12-numpy -> rgx1gen11/rattler-py3.12-numpy]                    |
| -        | 196±1ns     | 176±1ns     |    0.9  | benchmarks.time_ranges_multi(10, 'range') [rgx1gen11/virtualenv-py3.12-numpy -> rgx1gen11/rattler-py3.12-numpy]                     |
|          | 3.39±0.03μs | 3.09±0.03μs |    0.91 | benchmarks.time_ranges_multi(100, 'arange') [rgx1gen11/virtualenv-py3.12-numpy -> rgx1gen11/rattler-py3.12-numpy]                   |
| -        | 532±1ns     | 432±1ns     |    0.81 | benchmarks.time_ranges_multi(100, 'range') [rgx1gen11/virtualenv-py3.12-numpy -> rgx1gen11/rattler-py3.12-numpy]                    |
|          | 1.18±0μs    | 1.08±0μs    |    0.91 | benchmarks.time_sort(10) [rgx1gen11/virtualenv-py3.12-numpy -> rgx1gen11/rattler-py3.12-numpy]                                      |
| -        | 1.83±0.01μs | 1.63±0.01μs |    0.89 | benchmarks.time_sort(100) [rgx1gen11/virtualenv-py3.12-numpy -> rgx1gen11/rattler-py3.12-numpy]                                     |
```

### Consuming a single result file

Can be useful for exporting to other dashboards, or internally for further
inspection.

``` sh
➜ asv-spyglass to-df tests/data/d6b286b8-rattler-py3.12-numpy.json tests/data/d6b286b8_asv_samples_benchmarks.json
shape: (16, 17)
| benchmark_base                 | name                           | result    | units   | machine   | env                  | version                       | ci_99_a   | ci_99_b   | q_25      | q_75      | number | repeat | samples | param_size | param_n | param_func_name |
|--------------------------------|--------------------------------|-----------|---------|-----------|----------------------|-------------------------------|-----------|-----------|-----------|-----------|--------|--------|---------|------------|---------|-----------------|
| benchmarks.TimeSuiteDecoratorS | benchmarks.TimeSuiteDecoratorS | 1.3738e-7 | seconds | rgx1gen11 | rattler-py3.12-numpy | 64746c9051ff76aa879b428c27b42 | 1.3444e-7 | 1.4947e-7 | 1.3621e-7 | 1.4310e-7 | 67364  | 10     | null    | 10         | null    | null            |
| ingle.time_keys                | ingle.time_keys(10)            |           |         |           |                      | 47e8ed976c44a40579ae9...      |           |           |           |           |        |        |         |            |         |                 |
| benchmarks.TimeSuiteDecoratorS | benchmarks.TimeSuiteDecoratorS | 5.4292e-7 | seconds | rgx1gen11 | rattler-py3.12-numpy | 64746c9051ff76aa879b428c27b42 | 5.3813e-7 | 5.4586e-7 | 5.4190e-7 | 5.4495e-7 | 16815  | 10     | null    | 100        | null    | null            |
| ingle.time_keys                | ingle.time_keys(100)           |           |         |           |                      | 47e8ed976c44a40579ae9...      |           |           |           |           |        |        |         |            |         |                 |
| benchmarks.TimeSuiteDecoratorS | benchmarks.TimeSuiteDecoratorS | 0.000001  | seconds | rgx1gen11 | rattler-py3.12-numpy | 64746c9051ff76aa879b428c27b42 | 0.000001  | 0.000001  | 0.000001  | 0.000001  | 8960   | 10     | null    | 200        | null    | null            |
| ingle.time_keys                | ingle.time_keys(200)           |           |         |           |                      | 47e8ed976c44a40579ae9...      |           |           |           |           |        |        |         |            |         |                 |
| benchmarks.TimeSuiteDecoratorS | benchmarks.TimeSuiteDecoratorS | 1.8705e-7 | seconds | rgx1gen11 | rattler-py3.12-numpy | ab162b6142a1390a0e2a667ed8d2d | 1.8023e-7 | 1.9282e-7 | 1.8595e-7 | 1.9121e-7 | 63961  | 10     | null    | 10         | null    | null            |
| ingle.time_values              | ingle.time_values(10...        |           |         |           |                      | 3285f77152d9caa559b4f...      |           |           |           |           |        |        |         |            |         |                 |
| benchmarks.TimeSuiteDecoratorS | benchmarks.TimeSuiteDecoratorS | 7.8471e-7 | seconds | rgx1gen11 | rattler-py3.12-numpy | ab162b6142a1390a0e2a667ed8d2d | 7.7445e-7 | 7.9307e-7 | 7.8003e-7 | 7.8758e-7 | 15516  | 10     | null    | 100        | null    | null            |
| ingle.time_values              | ingle.time_values(10...        |           |         |           |                      | 3285f77152d9caa559b4f...      |           |           |           |           |        |        |         |            |         |                 |
| ...                            | ...                            | ...       | ...     | ...       | ...                  | ...                           | ...       | ...       | ...       | ...       | ...    | ...    | ...     | ...        | ...     | ...             |
| benchmarks.time_ranges_multi   | benchmarks.time_ranges_multi(1 | 0.000001  | seconds | rgx1gen11 | rattler-py3.12-numpy | f9ae8b134446c273c0d3eb1e90246 | 0.000001  | 0.000001  | 0.000001  | 0.000001  | 9631   | 10     | null    | null       | 10      | 'arange'        |
|                                | 0, 'arange')                   |           |         |           |                      | ae0d6f99389d06119dfe4...      |           |           |           |           |        |        |         |            |         |                 |
| benchmarks.time_ranges_multi   | benchmarks.time_ranges_multi(1 | 4.3222e-7 | seconds | rgx1gen11 | rattler-py3.12-numpy | f9ae8b134446c273c0d3eb1e90246 | 4.3157e-7 | 4.3557e-7 | 4.3176e-7 | 4.3420e-7 | 20588  | 10     | null    | null       | 100     | 'range'         |
|                                | 00, 'range')                   |           |         |           |                      | ae0d6f99389d06119dfe4...      |           |           |           |           |        |        |         |            |         |                 |
| benchmarks.time_ranges_multi   | benchmarks.time_ranges_multi(1 | 0.000003  | seconds | rgx1gen11 | rattler-py3.12-numpy | f9ae8b134446c273c0d3eb1e90246 | 0.000003  | 0.000003  | 0.000003  | 0.000003  | 3042   | 10     | null    | null       | 100     | 'arange'        |
|                                | 00, 'arange')                  |           |         |           |                      | ae0d6f99389d06119dfe4...      |           |           |           |           |        |        |         |            |         |                 |
| benchmarks.time_sort           | benchmarks.time_sort(10)       | 0.000001  | seconds | rgx1gen11 | rattler-py3.12-numpy | 60785bf757da0254d857b696482db | 0.000001  | 0.000001  | 0.000001  | 0.000001  | 9345   | 10     | null    | null       | 10      | null            |
|                                |                                |           |         |           |                      | 7a25509a5b28a2c9d2a54...      |           |           |           |           |        |        |         |            |         |                 |
| benchmarks.time_sort           | benchmarks.time_sort(100)      | 0.000002  | seconds | rgx1gen11 | rattler-py3.12-numpy | 60785bf757da0254d857b696482db | 0.000002  | 0.000002  | 0.000002  | 0.000002  | 5828   | 10     | null    | null       | 100     | null            |
|                                |                                |           |         |           |                      | 7a25509a5b28a2c9d2a54...      |           |           |           |           |        |        |         |            |         |                 |
```



# Contributions

All contributions are welcome, this includes code and documentation
contributions but also questions or other clarifications. Note that we expect
all contributors to follow our [Code of
Conduct](https://github.com/airspeed-velocity/asv_spyglass/blob/main/CODE_OF_CONDUCT.md).

## Developing locally

### Testing

Since the output of these are mostly text oriented, and the inputs are `json`,
these are handled via a mixture of reading known data and using golden master
testing aka approval testing. Thus `pytest` with `pytest-datadir` and
`ApprovalTests.Python` is used.

### Linting and Formatting

A `pre-commit` job is setup on CI to enforce consistent styles, so it is best to
set it up locally as well (using [pipx](https://pypa.github.io/pipx/) for isolation):

```sh
# Run before commiting
pipx run pre-commit run --all-files
# Or install the git hook to enforce this
pipx run pre-commit install
```
