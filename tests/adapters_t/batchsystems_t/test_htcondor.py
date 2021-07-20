from tests.utilities.utilities import run_async
from tests.utilities.utilities import mock_executor_run_command
from tardis.adapters.batchsystems.htcondor import HTCondorAdapter
from tardis.adapters.batchsystems.htcondor import htcondor_status_updater
from tardis.interfaces.batchsystemadapter import MachineStatus
from tardis.exceptions.executorexceptions import CommandExecutionFailure
from tardis.utilities.attributedict import AttributeDict

from functools import partial
from shlex import quote
from unittest.mock import patch
from unittest import TestCase

import logging

CPU_RATIO = 0.9
MEMORY_RATIO = 0.8
CONDOR_RETURN = "\n".join(
    [
        f"test\tslot1@test\tUnclaimed\tIdle\tundefined\t{CPU_RATIO}\t{MEMORY_RATIO}",  # noqa: B950
        f"test_drain\tslot1@test\tDrained\tRetiring\tundefined\t{CPU_RATIO}\t{MEMORY_RATIO}",  # noqa: B950
        f"test_drained\tslot1@test\tDrained\tIdle\tundefined\t{CPU_RATIO}\t{MEMORY_RATIO}",  # noqa: B950
        f"test_owner\tslot1@test\tOwner\tIdle\tundefined\t{CPU_RATIO}\t{MEMORY_RATIO}",  # noqa: B950
        f"test_uuid_plus\tslot1@test_uuid@test\tUnclaimed\tIdle\ttest_uuid\t{CPU_RATIO}\t{MEMORY_RATIO}",  # noqa: B950
        f"test_undefined\tslot1@test\tUnclaimed\tIdle\tundefined\tundefined\t{MEMORY_RATIO}",  # noqa: B950
        f"test_error\tslot1@test\tUnclaimed\tIdle\tundefined\terror\t{MEMORY_RATIO}",  # noqa: B950
        "exoscale-26d361290f\tslot1@exoscale-26d361290f\tUnclaimed\tIdle\tundefined\t0.125\t0.125",  # noqa: B950
    ]
)


class TestHTCondorAdapter(TestCase):
    mock_config_patcher = None
    mock_executor_patcher = None

    @classmethod
    def setUpClass(cls):
        cls.mock_config_patcher = patch(
            "tardis.adapters.batchsystems.htcondor.Configuration"
        )
        cls.mock_executor_patcher = patch(
            "tardis.adapters.batchsystems.htcondor.ShellExecutor"
        )
        cls.mock_executor = cls.mock_executor_patcher.start()
        cls.mock_config = cls.mock_config_patcher.start()

    @classmethod
    def tearDownClass(cls):
        cls.mock_config_patcher.stop()
        cls.mock_executor_patcher.stop()

    def setUp(self):
        self.cpu_ratio = CPU_RATIO
        self.memory_ratio = MEMORY_RATIO
        self.command = (
            "condor_status -af:t Machine Name State Activity TardisDroneUuid "
            "'Real(TotalSlotCpus-Cpus)/TotalSlotCpus' "
            "'Real(TotalSlotMemory-Memory)/TotalSlotMemory' -constraint PartitionableSlot=?=True"  # noqa: B950
            " -pool my-htcondor.local -test"
        )

        self.command_wo_options = (
            "condor_status -af:t Machine Name State Activity TardisDroneUuid "
            "'Real(TotalSlotCpus-Cpus)/TotalSlotCpus' "
            "'Real(TotalSlotMemory-Memory)/TotalSlotMemory' -constraint PartitionableSlot=?=True"  # noqa: B950
        )

        self.setup_config_mock(options={"pool": "my-htcondor.local", "test": None})

        self.htcondor_adapter = HTCondorAdapter()

    def tearDown(self):
        self.mock_executor.reset_mock()

    def setup_config_mock(self, options=None):
        self.config = self.mock_config.return_value
        self.config.BatchSystem.executor = self.mock_executor.return_value
        self.config.BatchSystem.ratios = {
            "cpu_ratio": "Real(TotalSlotCpus-Cpus)/TotalSlotCpus",
            "memory_ratio": "Real(TotalSlotMemory-Memory)/TotalSlotMemory",
        }
        self.config.BatchSystem.max_age = 10
        if options:
            self.config.BatchSystem.options = options
        else:
            self.config.BatchSystem.options = {}

    def test_disintegrate_machine(self):
        self.assertIsNone(
            run_async(self.htcondor_adapter.disintegrate_machine, drone_uuid="test")
        )

    @mock_executor_run_command(stdout=CONDOR_RETURN)
    def test_drain_machine(self):
        run_async(self.htcondor_adapter.drain_machine, drone_uuid="test")
        self.mock_executor.return_value.run_command.assert_called_with(
            "condor_drain -pool my-htcondor.local -test -graceful slot1@test"
        )

        self.mock_executor.reset_mock()

        run_async(self.htcondor_adapter.drain_machine, drone_uuid="test_uuid")
        self.mock_executor.return_value.run_command.assert_called_with(
            "condor_drain -pool my-htcondor.local -test -graceful slot1@test_uuid@test"
        )
        self.assertIsNone(
            run_async(self.htcondor_adapter.drain_machine, drone_uuid="not_exists")
        )
        self.mock_executor.return_value.run_command.side_effect = (
            CommandExecutionFailure(
                message="Does not exists", exit_code=1, stderr="Does not exists"
            )
        )
        with self.assertLogs(level=logging.WARNING):
            self.assertIsNone(
                run_async(self.htcondor_adapter.drain_machine, drone_uuid="test")
            )

        self.mock_executor.return_value.run_command.side_effect = (
            CommandExecutionFailure(
                message="Unhandled error", exit_code=2, stderr="Unhandled error"
            )
        )

        with self.assertRaises(CommandExecutionFailure):
            with self.assertLogs(level=logging.CRITICAL):
                self.assertIsNone(
                    run_async(self.htcondor_adapter.drain_machine, drone_uuid="test")
                )

        self.mock_executor.return_value.run_command.side_effect = None

    #  @mock_executor_run_command(stdout=CONDOR_RETURN)
    def test_drain_machine_without_options(self):
        self.setup_config_mock()
        self.htcondor_adapter = HTCondorAdapter()

        run_async(self.htcondor_adapter.drain_machine, drone_uuid="test")
        self.mock_executor.return_value.run_command.assert_called_with(
            "condor_drain -graceful slot1@test"
        )

        self.mock_executor.reset_mock()

        run_async(self.htcondor_adapter.drain_machine, drone_uuid="test_uuid")
        self.mock_executor.return_value.run_command.assert_called_with(
            "condor_drain -graceful slot1@test_uuid@test"
        )

    def test_integrate_machine(self):
        self.assertIsNone(
            run_async(self.htcondor_adapter.integrate_machine, drone_uuid="test")
        )

    @mock_executor_run_command(stdout=CONDOR_RETURN)
    def test_get_resource_ratios(self):
        self.assertCountEqual(
            list(
                run_async(self.htcondor_adapter.get_resource_ratios, drone_uuid="test")
            ),
            [self.cpu_ratio, self.memory_ratio],
        )
        self.mock_executor.return_value.run_command.assert_called_with(self.command)
        self.mock_executor.reset_mock()

        self.assertEqual(
            run_async(
                self.htcondor_adapter.get_resource_ratios, drone_uuid="not_exists"
            ),
            [],
        )
        self.mock_executor.return_value.run_command.assert_not_called()
        self.mock_executor.reset_mock()

        self.assertEqual(
            run_async(
                self.htcondor_adapter.get_resource_ratios, drone_uuid="test_undefined"
            ),
            [],
        )
        self.mock_executor.return_value.run_command.assert_not_called()
        self.mock_executor.reset_mock()

        self.assertEqual(
            run_async(
                self.htcondor_adapter.get_resource_ratios, drone_uuid="test_error"
            ),
            [],
        )

    @mock_executor_run_command(stdout=CONDOR_RETURN)
    def test_get_resource_ratios_without_options(self):
        self.setup_config_mock()
        del self.config.BatchSystem.options
        self.htcondor_adapter = HTCondorAdapter()

        self.assertCountEqual(
            list(
                run_async(self.htcondor_adapter.get_resource_ratios, drone_uuid="test")
            ),
            [self.cpu_ratio, self.memory_ratio],
        )

        self.mock_executor.return_value.run_command.assert_called_with(
            self.command_wo_options
        )

    @mock_executor_run_command(stdout=CONDOR_RETURN)
    def test_get_allocation(self):
        self.assertEqual(
            run_async(self.htcondor_adapter.get_allocation, drone_uuid="test"),
            max([self.cpu_ratio, self.memory_ratio]),
        )
        self.mock_executor.return_value.run_command.assert_called_with(self.command)

    @mock_executor_run_command(stdout=CONDOR_RETURN)
    def test_get_machine_status(self):
        self.assertEqual(
            run_async(self.htcondor_adapter.get_machine_status, drone_uuid="test"),
            MachineStatus.Available,
        )
        self.mock_executor.return_value.run_command.assert_called_with(self.command)
        self.mock_executor.reset_mock()
        self.assertEqual(
            run_async(
                self.htcondor_adapter.get_machine_status, drone_uuid="not_exists"
            ),
            MachineStatus.NotAvailable,
        )
        self.mock_executor.reset_mock()
        self.assertEqual(
            run_async(
                self.htcondor_adapter.get_machine_status, drone_uuid="test_drain"
            ),
            MachineStatus.Draining,
        )
        self.mock_executor.reset_mock()
        self.assertEqual(
            run_async(
                self.htcondor_adapter.get_machine_status, drone_uuid="test_drained"
            ),
            MachineStatus.Drained,
        )
        self.mock_executor.reset_mock()
        self.assertEqual(
            run_async(
                self.htcondor_adapter.get_machine_status, drone_uuid="test_owner"
            ),
            MachineStatus.NotAvailable,
        )
        self.mock_executor.reset_mock()

        self.assertEqual(
            run_async(self.htcondor_adapter.get_machine_status, drone_uuid="test_uuid"),
            MachineStatus.Available,
        )
        self.mock_executor.reset_mock()

        self.mock_executor.return_value.run_command.side_effect = (
            CommandExecutionFailure(message="Test", exit_code=123, stderr="Test")
        )
        with self.assertLogs(level=logging.WARNING):
            with self.assertRaises(CommandExecutionFailure):
                attributes = {
                    "Machine": "Machine",
                    "State": "State",
                    "Activity": "Activity",
                    "TardisDroneUuid": "TardisDroneUuid",
                }
                # Escape htcondor expressions and add them to attributes
                attributes.update(
                    {
                        key: quote(value)
                        for key, value in self.config.BatchSystem.ratios.items()
                    }
                )
                run_async(
                    partial(
                        htcondor_status_updater,
                        self.config.BatchSystem.options,
                        attributes,
                        self.mock_executor.return_value,
                    )
                )
                self.mock_executor.return_value.run_command.assert_called_with(
                    self.command
                )
        self.mock_executor.return_value.run_command.side_effect = None

    @mock_executor_run_command(stdout=CONDOR_RETURN)
    def test_get_utilisation(self):
        self.assertEqual(
            run_async(self.htcondor_adapter.get_utilisation, drone_uuid="test"),
            min([self.cpu_ratio, self.memory_ratio]),
        )
        self.mock_executor.return_value.run_command.assert_called_with(self.command)

    def test_machine_meta_data_translation_mapping(self):
        self.assertEqual(
            AttributeDict(Cores=1, Memory=1024, Disk=1024 * 1024),
            self.htcondor_adapter.machine_meta_data_translation_mapping,
        )
