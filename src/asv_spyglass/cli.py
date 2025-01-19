import click

from asv_spyglass.compare import do_compare


@click.command()
@click.argument("b1", type=click.Path(exists=True), required=True)
@click.argument("b2", type=click.Path(exists=True), required=True)
@click.argument("bconf", type=click.Path(exists=True), required=True)
@click.option(
    "--factor",
    default=1.1,
    show_default=True,
    help="Factor for determining significant changes.",
)
@click.option(
    "--split",
    is_flag=True,
    help="Split output by improvement/regression.",
)
@click.option(
    "--only-changed",
    is_flag=True,
    help="Only show changed benchmarks.",
)
@click.option(
    "--sort",
    type=click.Choice(["default", "ratio", "name"]),
    default="default",
    show_default=True,
    help="Sort output by change, ratio, or name.",
)
def cli(b1, b2, bconf, factor, split, only_changed, sort):
    """
    Compare two ASV result files.
    """
    do_compare(b1, b2, bconf, factor, split, only_changed, sort)
