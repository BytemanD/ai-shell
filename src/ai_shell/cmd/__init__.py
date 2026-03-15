import logging

import click

log_levels = [logging.WARNING, logging.INFO, logging.DEBUG]


@click.group(
    context_settings=dict(help_option_names=["-h", "--help"], show_default=True)
)
@click.option("-v", "--verbose", count=True)
def cli(verbose: int):
    """AI-SHELL: 一个智能终端工具"""

    logging.basicConfig(
        level=log_levels[min(verbose, len(log_levels) - 1)],
        format="%(asctime)s | %(levelname)s | %(name)s - %(message)s",
    )
