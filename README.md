# About [![Documentation](https://img.shields.io/badge/Documentation-latest-brightgreen?style=for-the-badge)](https://asv.readthedocs.io/projects/asv-spyglass/en/latest/)

`asv` output file comparer, for comparing across different environments or runs.

For other functionality, refer to the `asv` package or consider writing an
extension.

## Basic usage

### Comparing two benchmarks

This is agnostic to environment.

``` sh
asv-spyglass compare tests/data/d6b286b8-virtualenv-py3.12-numpy.json tests/data/d6b286b8-rattler-py3.12-numpy.json tests/data/d6b286b8_asv_samples_benchmarks.json


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
                                     benchmark_base                                               name        result    units    machine                   env  ... number  repeat  samples  param_size  param_n  param_func_name
0     benchmarks.TimeSuiteDecoratorSingle.time_keys  benchmarks.TimeSuiteDecoratorSingle.time_keys(10)  1.373785e-07  seconds  rgx1gen11  rattler-py3.12-numpy  ...  67364      10     None          10      NaN              NaN
1     benchmarks.TimeSuiteDecoratorSingle.time_keys  benchmarks.TimeSuiteDecoratorSingle.time_keys(...  5.429163e-07  seconds  rgx1gen11  rattler-py3.12-numpy  ...  16815      10     None         100      NaN              NaN
2     benchmarks.TimeSuiteDecoratorSingle.time_keys  benchmarks.TimeSuiteDecoratorSingle.time_keys(...  1.072828e-06  seconds  rgx1gen11  rattler-py3.12-numpy  ...   8960      10     None         200      NaN              NaN
3   benchmarks.TimeSuiteDecoratorSingle.time_values  benchmarks.TimeSuiteDecoratorSingle.time_value...  1.870524e-07  seconds  rgx1gen11  rattler-py3.12-numpy  ...  63961      10     None          10      NaN              NaN
4   benchmarks.TimeSuiteDecoratorSingle.time_values  benchmarks.TimeSuiteDecoratorSingle.time_value...  7.847096e-07  seconds  rgx1gen11  rattler-py3.12-numpy  ...  15516      10     None         100      NaN              NaN
5   benchmarks.TimeSuiteDecoratorSingle.time_values  benchmarks.TimeSuiteDecoratorSingle.time_value...  1.461304e-06  seconds  rgx1gen11  rattler-py3.12-numpy  ...   8748      10     None         200      NaN              NaN
6    benchmarks.TimeSuiteMultiDecorator.time_ranges  benchmarks.TimeSuiteMultiDecorator.time_ranges...  2.309674e-07  seconds  rgx1gen11  rattler-py3.12-numpy  ...  51698      10     None         NaN       10          'range'
7    benchmarks.TimeSuiteMultiDecorator.time_ranges  benchmarks.TimeSuiteMultiDecorator.time_ranges...  1.373753e-06  seconds  rgx1gen11  rattler-py3.12-numpy  ...   9417      10     None         NaN       10         'arange'
8    benchmarks.TimeSuiteMultiDecorator.time_ranges  benchmarks.TimeSuiteMultiDecorator.time_ranges...  6.507371e-07  seconds  rgx1gen11  rattler-py3.12-numpy  ...  20005      10     None         NaN      100          'range'
9    benchmarks.TimeSuiteMultiDecorator.time_ranges  benchmarks.TimeSuiteMultiDecorator.time_ranges...  3.831307e-06  seconds  rgx1gen11  rattler-py3.12-numpy  ...   3213      10     None         NaN      100         'arange'
10                     benchmarks.time_ranges_multi          benchmarks.time_ranges_multi(10, 'range')  1.759081e-07  seconds  rgx1gen11  rattler-py3.12-numpy  ...  54349      10     None         NaN       10          'range'
11                     benchmarks.time_ranges_multi         benchmarks.time_ranges_multi(10, 'arange')  1.041947e-06  seconds  rgx1gen11  rattler-py3.12-numpy  ...   9631      10     None         NaN       10         'arange'
12                     benchmarks.time_ranges_multi         benchmarks.time_ranges_multi(100, 'range')  4.322196e-07  seconds  rgx1gen11  rattler-py3.12-numpy  ...  20588      10     None         NaN      100          'range'
13                     benchmarks.time_ranges_multi        benchmarks.time_ranges_multi(100, 'arange')  3.086801e-06  seconds  rgx1gen11  rattler-py3.12-numpy  ...   3042      10     None         NaN      100         'arange'
14                             benchmarks.time_sort                           benchmarks.time_sort(10)  1.075453e-06  seconds  rgx1gen11  rattler-py3.12-numpy  ...   9345      10     None         NaN       10              NaN
15                             benchmarks.time_sort                          benchmarks.time_sort(100)  1.631129e-06  seconds  rgx1gen11  rattler-py3.12-numpy  ...   5828      10     None         NaN      100              NaN
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
