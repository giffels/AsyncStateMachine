.. Created by changelog.py at 2021-05-14, command
   '/Users/giffler/.cache/pre-commit/repor6pnmwlm/py_env-python3.9/bin/changelog docs/source/changes compile --output=docs/source/changelog.rst'
   based on the format of 'https://keepachangelog.com/'

#########
CHANGELOG
#########

[Unreleased] - 2021-05-14
=========================

Added
-----

* An optional and per site configurable drone heartbeat interval has been added

Fixed
-----

* Fixes a bug that get_resource_ratios raised a ValueError
* Fixes a bug that the drone_minimum_lifetime parameter is not working as described in the documentation
* Fixes a bug in the HTCondor Site Adapter which leads to wrong requirements when using non HTCondor OBS

[0.5.0] - 2020-12-09
====================

Added
-----

* Export tardis environment variable via slurm site adapter
* Added support for Slurm overlay batch system

[0.4.0] - 2020-06-03
====================

Added
-----

* Added an example HTCondor jdl for the HTCondor site adapter
* Added a prometheus monitoring plugin
* Enable support for `sbatch` command line options in the Slurm site adapter
* Add ssh connection sharing to `SSHExecutor` in order to re-use existing connection

Changed
-------

* Added log channels and adjusted log levels according to the conventions in `COBalD` documentation
* The Moab adapter can now be configured to use different startup commands for each machine type.
* The SLURM adapter can now be configured to use different startup commands for each machine type.

Fixed
-----

* Fixed the exception handling of `ConnectionResetError` in `SSHExecutor`
* Fixed the resource status translation of the moab site adapter

[0.3.0] - 2020-02-26
====================

Added
-----

* Add support for Python 3.8
* Register pool factory as `COBalD` yaml plugin
* Add support for COBalD legacy object initialisation
* The machine name has been added as a default tag in the telegraf monitoring plugin, can be overwritten.
* An optional and per site configurable drone minimum lifetime has been added
* Add the possibility to use an unified `COBalD` and `TARDIS` configuration

Fixed
-----

* Fix draining of slots having a startd name
* Fix the translation of cloud init scripts into base64 encoded strings
* Use utilisation as weight in composite pools
* Allow removal of booting drones if demand drops to zero
* The `CleanupState` is now taking into account the status of the resource for state transitions
* Improved logging of the `HTCondor` batch system adapter and the status changes of the drones
* Fix the handling of the termination of vanished resources
* Fix state transitions for jobs retried by HTCondor
* Fix state transitions and refactoring of the SLURM site adapter
