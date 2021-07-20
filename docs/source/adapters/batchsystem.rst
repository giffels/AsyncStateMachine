.. _ref_batch_system_adapter:

=====================
Batch System Adapters
=====================

Fake Batch System Adapter
-------------------------

.. |FakeBatchSystemAdapter.get_utilisation| replace:: :py:meth:`~tardis.adapters.batchsystems.fakebatchsystem.FakeBatchSystemAdapter.get_utilisation`

.. |FakeBatchSystemAdapter.get_allocation| replace:: :py:meth:`~tardis.adapters.batchsystems.fakebatchsystem.FakeBatchSystemAdapter.get_allocation`

.. |FakeBatchSystemAdapter.get_machine_status| replace:: :py:meth:`~tardis.adapters.batchsystems.fakebatchsystem.FakeBatchSystemAdapter.get_machine_status`

.. container:: left-col

    The :py:class:`~tardis.adapters.batchsystems.fakebatchsystem.FakeBatchSystemAdapter`
    implements a batch system adapter that mocks the response of hypothetical batch system.
    It can be used for testing purposes and as a demonstrator in workshops and tutorials.

    The mocked response to the |FakeBatchSystemAdapter.get_allocation|, |FakeBatchSystemAdapter.get_utilisation| and
    |FakeBatchSystemAdapter.get_machine_status| API calls is configurable statically in the adapter configuration.

Available configuration options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. content-tabs:: left-col

    +----------------+---------------------------------------------------------------------+-----------------+
    | Option         | Short Description                                                   | Requirement     |
    +================+=====================================================================+=================+
    | adapter        | Name of the adapter (FakeBatchSystem)                               |  **Required**   |
    +----------------+---------------------------------------------------------------------+-----------------+
    | allocation     | Mocked response to |FakeBatchSystemAdapter.get_allocation| call     |  **Required**   |
    +----------------+---------------------------------------------------------------------+-----------------+
    | utilisation    | Mocked response to |FakeBatchSystemAdapter.get_utilisation| call    |  **Required**   |
    +----------------+---------------------------------------------------------------------+-----------------+
    | machine_status | Mocked response to |FakeBatchSystemAdapter.get_machine_status| call |  **Required**   |
    +----------------+---------------------------------------------------------------------+-----------------+

.. container:: content-tabs right-col

    .. rubric:: Example configuration

    .. code-block:: yaml

        BatchSystem:
            adapter: FakeBatchSystem
            allocation: 1.0
            utilisation: 1.0
            machine_status: Available

HTCondor Batch System Adapter
-----------------------------

.. content-tabs:: left-col

    .. |HTCondorAdapter.get_utilisation| replace:: :py:meth:`~tardis.adapters.batchsystems.htcondor.HTCondorAdapter.get_utilisation`

    .. |HTCondorAdapter.get_allocation| replace:: :py:meth:`~tardis.adapters.batchsystems.htcondor.HTCondorAdapter.get_allocation`

    .. |HTCondorAdapter.get_machine_status| replace:: :py:meth:`~tardis.adapters.batchsystems.htcondor.HTCondorAdapter.get_machine_status`

    The :py:class:`~tardis.adapters.batchsystems.htcondor.HTCondorAdapter` implements the TARDIS interface to dynamically
    integrate and manage opportunistic resources with the HTCondor batch system.

    Information provider for the API calls |HTCondorAdapter.get_utilisation|, |HTCondorAdapter.get_allocation| and
    |HTCondorAdapter.get_machine_status| is the HTCondor ``condor_status`` command, which is called asynchronously and its
    output is cached for a configurable time ``max_age``.

    |HTCondorAdapter.get_machine_status| returns the status of the worker node by taking into account the HTCondor
    ClassAds ``State`` and ``Activity``. It can take the states ``Available``, ``Draining``, ``Drained`` and
    ``NotAvailable``.

    The allocation and utilisation of a worker node is defined as maximum and minimum of the relative ratio of requested
    over total resources such as CPU, Memory, Disk, respectively. Which resource ratios to take into account can be
    configured via the ``ratios`` option. Any valid HTCondor expression that returns a floating point number is accepted.

.. content-tabs:: left-col

    Additional options for the condor_status call can be added by using the ``options`` option.

.. content-tabs:: right-col

    For example

    .. code-block:: yaml

        options:
          pool: htcondor.example

    translates into ``condor_status ... -pool htcondor.example``.

Available configuration options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. content-tabs:: left-col

    +----------------+-------------------------------------------------------------------------+-----------------+
    | Option         | Short Description                                                       | Requirement     |
    +================+=========================================================================+=================+
    | adapter        | Name of the adapter (HTCondor)                                          |  **Required**   |
    +----------------+-------------------------------------------------------------------------+-----------------+
    | max_age        | Maximum age of the cached ``condor_status`` information in minutes      |  **Required**   |
    +----------------+-------------------------------------------------------------------------+-----------------+
    | ratios         | HTCondor expressions used to determine allocation and utilisation       |  **Required**   |
    +----------------+-------------------------------------------------------------------------+-----------------+
    | options        | Additional command line options to add to the ``condor_status`` command |  **Optional**   |
    +----------------+-------------------------------------------------------------------------+-----------------+
    | executor       | The |executor| used to run commands of the batch system.                |  **Optional**   |
    +                +                                                                         +                 +
    |                | Default: ShellExecutor is used!                                         |                 |
    +----------------+-------------------------------------------------------------------------+-----------------+

.. content-tabs:: right-col

    .. rubric:: Example configuration

    .. code-block:: yaml

        BatchSystem:
            adapter: HTCondor
            max_age: 1
            ratios:
                cpu_ratio: Real(TotalSlotCpus-Cpus)/TotalSlotCpus
                memory_ratio: Real(TotalSlotMemory-Memory)/TotalSlotMemory
            options:
                pool: my-htcondor.mysite.mydomain

SLURM Batch System Adapter
-----------------------------

.. content-tabs:: left-col

    .. |SlurmAdapter.get_utilisation| replace:: :py:meth:`~tardis.adapters.batchsystems.slurm.SlurmAdapter.get_utilisation`

    .. |SlurmAdapter.get_allocation| replace:: :py:meth:`~tardis.adapters.batchsystems.slurm.SlurmAdapter.get_allocation`

    .. |SlurmAdapter.get_machine_status| replace:: :py:meth:`~tardis.adapters.batchsystems.slurm.SlurmAdapter.get_machine_status`

    The :py:class:`~tardis.adapters.batchsystems.slurm.SlurmAdapter` implements the TARDIS interface to dynamically
    integrate and manage opportunistic resources with the Slurm batch system.

    The Slurm command ``sinfo`` is used to obtain the information provided by the calls |SlurmAdapter.get_utilisation|,
    |SlurmAdapter.get_allocation| and |SlurmAdapter.get_machine_status|. The call is performed asynchronously and its
    output is cached for a configurable time ``max_age``.

    |SlurmAdapter.get_machine_status| returns the status of the worker node which can be either ``Available``, ``Draining``,
    ``Drained`` or ``NotAvailable``.

    The allocation and utilisation of a worker node is defined as maximum and minimum of the relative ratio of requested
    over total resources CPU and Memory, respectively. The ratios are computed as allocated resource divided by total
    available resource.

.. content-tabs:: left-col

    Additional arguments for the ``sinfo`` call can be appended by adding the ``options`` MappingNode. This supports
    both ``long`` and ``short`` arguments.

    .. Note::

        The alignment of colons in the examples to the right is a simple coincidence and for parsing ``yaml`` only the
        indentation is crucial.

.. content-tabs:: right-col

    For example

    .. code-block:: yaml

        options:
          long:
            partition: express

    translates into ``sinfo ... --partition=express`` and

    .. code-block:: yaml

        options:
          short:
            p: express

    to ``sinfo ... -p express``.

Available configuration options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. content-tabs:: left-col

    +----------------+---------------------------------------------------------------------------------------------------------------------------+-----------------+
    | Option         | Short Description                                                                                                         | Requirement     |
    +================+===========================================================================================================================+=================+
    | adapter        | Name of the adapter (Slurm)                                                                                               |  **Required**   |
    +----------------+---------------------------------------------------------------------------------------------------------------------------+-----------------+
    | max_age        | Maximum age of the cached ``sinfo`` information in minutes                                                                |  **Required**   |
    +----------------+---------------------------------------------------------------------------------------------------------------------------+-----------------+
    | options        | Additional command line options to add to the ``sinfo`` command. `long` and `short` arguments are supported (see example) |  **Optional**   |
    +----------------+---------------------------------------------------------------------------------------------------------------------------+-----------------+
    | executor       | The |executor| used to run commands of the batch system.                                                                  |  **Optional**   |
    +                +                                                                                                                           +                 +
    |                | Default: ShellExecutor is used!                                                                                           |                 |
    +----------------+---------------------------------------------------------------------------------------------------------------------------+-----------------+

.. content-tabs:: right-col

    .. rubric:: Example configuration

    .. code-block:: yaml

        BatchSystem:
            adapter: Slurm
            max_age: 1
            options:
              long:
                partition: express

.. content-tabs:: left-col

    Your favorite batch system is currently not supported?
    Please, have a look at
    :ref:`how to contribute.<ref_contribute_batch_system_adapter>`
