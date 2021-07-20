from tardis.utilities.attributedict import AttributeDict
from tardis.utilities.utils import htcondor_cmd_option_formatter
from tardis.utilities.utils import csv_parser
from tardis.utilities.utils import submit_cmd_option_formatter

from unittest import TestCase


class TestHTCondorCMDOptionFormatter(TestCase):
    def test_htcondor_cmd_option_formatter(self):
        options = AttributeDict(pool="my-htcondor.local", test=None)
        option_string = htcondor_cmd_option_formatter(options)

        self.assertEqual(option_string, "-pool my-htcondor.local -test")

        options = AttributeDict()
        option_string = htcondor_cmd_option_formatter(options)

        self.assertEqual(option_string, "")


class TestCSVParser(TestCase):
    def test_csv_parser_htcondor(self):
        htcondor_input = "\n".join(
            [
                "exoscale-26d361290f\tUnclaimed\tIdle\t0.125\t0.125",
                "test_replace\tOwner\tIdle\tundefined\tundefined",
            ]
        )

        parsed_rows = csv_parser(
            input_csv=htcondor_input,
            fieldnames=("Machine", "State", "Activity", "Test1", "Test2"),
            replacements=dict(undefined=None),
        )

        self.assertEqual(
            next(parsed_rows),
            dict(
                Machine="exoscale-26d361290f",
                State="Unclaimed",
                Activity="Idle",
                Test1="0.125",
                Test2="0.125",
            ),
        )

        self.assertEqual(
            next(parsed_rows),
            dict(
                Machine="test_replace",
                State="Owner",
                Activity="Idle",
                Test1=None,
                Test2=None,
            ),
        )

    def test_csv_parser_slurm(self):
        slurm_input = "\n".join(
            [
                "mixed  2/38/0/40  8000  10000  site-123  host-1    ",
                "idle   0/40/0/40     0  10000  site-124  host-2    ",
            ]
        )

        parsed_rows = csv_parser(
            input_csv=slurm_input,
            fieldnames=("State", "CPU", "AllocMem", "Memory", "Features", "NodeHost"),
            replacements=dict(undefined=None),
            delimiter=" ",
            skipinitialspace=True,
            skiptrailingspace=True,
        )

        self.assertEqual(
            next(parsed_rows),
            dict(
                State="mixed",
                CPU="2/38/0/40",
                AllocMem="8000",
                Memory="10000",
                Features="site-123",
                NodeHost="host-1",
            ),
        )

        self.assertEqual(
            next(parsed_rows),
            dict(
                State="idle",
                CPU="0/40/0/40",
                AllocMem="0",
                Memory="10000",
                Features="site-124",
                NodeHost="host-2",
            ),
        )


class TestSlurmCMDOptionFormatter(TestCase):
    def test_submit_cmd_option_formatter(self):
        options = AttributeDict()
        option_string = submit_cmd_option_formatter(options)

        self.assertEqual(option_string, "")

        options = AttributeDict(short=AttributeDict(foo="bar", test=None))
        option_string = submit_cmd_option_formatter(options)

        self.assertEqual(option_string, "-foo bar -test")

        options = AttributeDict(long=AttributeDict(foo="bar", test=None))
        option_string = submit_cmd_option_formatter(options)

        self.assertEqual(option_string, "--foo=bar --test")

        options = AttributeDict(
            short=AttributeDict(foo="bar", test=None),
            long=AttributeDict(foo_long="bar_long", test_long=None),
        )
        option_string = submit_cmd_option_formatter(options)

        self.assertEqual(
            option_string, "-foo bar -test --foo_long=bar_long --test_long"
        )
