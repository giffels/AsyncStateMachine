from .attributedict import AttributeDict

from io import StringIO
from typing import Any, Callable, List, TypeVar, Tuple


import csv
import logging

logger = logging.getLogger("cobald.runtime.tardis.utilities.utils")


def cmd_option_formatter(options: AttributeDict, prefix: str, separator: str) -> str:
    options = (
        f"{prefix}{name}{separator}{value}" if value is not None else f"{prefix}{name}"
        for name, value in options.items()
    )

    return " ".join(options)


def htcondor_cmd_option_formatter(options: AttributeDict) -> str:
    return cmd_option_formatter(options, prefix="-", separator=" ")


def csv_parser(
    input_csv: str,
    fieldnames: [List, Tuple],
    delimiter: str = "\t",
    replacements: dict = None,
    skipinitialspace: bool = False,
    skiptrailingspace: bool = False,
):
    """
    Parses CSV formatted input

    :param input_csv: CSV formatted input
    :type input_csv: str
    :param fieldnames: corresponding field names
    :type fieldnames: [List, Tuple]
    :param delimiter: delimiter between entries
    :type delimiter: str
    :param replacements: fields to be replaced
    :type replacements: dict
    :param skipinitialspace: ignore whitespace immediately following the delimiter
    :type skipinitialspace: bool
    :param skiptrailingspace: ignore whitespace at the end of each csv row
    :type skiptrailingspace: bool
    """
    if skiptrailingspace:
        input_csv = "\n".join((line.strip() for line in input_csv.splitlines()))

    replacements = replacements or {}
    with StringIO(input_csv) as csv_input:
        csv_reader = csv.DictReader(
            csv_input,
            fieldnames=fieldnames,
            delimiter=delimiter,
            skipinitialspace=skipinitialspace,
        )
        for row in csv_reader:
            yield {
                key: value if value not in replacements.keys() else replacements[value]
                for key, value in row.items()
            }


def machine_meta_data_translation(
    machine_meta_data: AttributeDict, meta_data_translation_mapping: AttributeDict
):
    """
    Helper function to translate units of the machine_meta_data to match the
    units required by the overlay batch system
    :param machine_meta_data: Machine Meta Data (Cores, Memory, Disk)
    :param meta_data_translation_mapping: Map used for the translation of meta
           data, contains conversion factors
    :return:
    :rtype: dict
    """
    try:
        return {
            key: meta_data_translation_mapping[key] * value
            for key, value in machine_meta_data.items()
        }
    except KeyError as ke:
        logger.critical(
            f"machine_meta_data_translation failed: no translation known for {ke}"
        )
        raise


def submit_cmd_option_formatter(options: AttributeDict) -> str:
    option_prefix = dict(short="-", long="--")
    option_separator = dict(short=" ", long="=")

    option_string = ""

    for option_type in ("short", "long"):
        try:
            tmp_option_string = cmd_option_formatter(
                getattr(options, option_type),
                prefix=option_prefix[option_type],
                separator=option_separator[option_type],
            )
        except AttributeError:
            pass
        else:
            # add additional space between short and long options
            if option_string:
                option_string += " "
            option_string += tmp_option_string

    return option_string.strip()


T = TypeVar("T")
sentinel = object()


def convert_to(
    value: Any, convert_to_type: Callable[[Any], T], default: Any = sentinel
) -> T:
    try:
        return convert_to_type(value)
    except ValueError:
        return default
