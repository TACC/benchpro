.. _user_setup:

============
User Setup
============

The BenchPRO site package should already be installed on most TACC systems. If it is not, contact ``mcawood@tacc.utexas.edu`` or install it from the benchpro-site_ repository. Assuming the site package is available, you need to install a local copy of the configuration and template files to use BenchPRO.

.. _benchpro-site: https://github.com/TACC/benchpro-site

TACC system site installs
^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
    :header-rows: 1

    * - System
      - Module Path
    * - Frontera
      - /scratch1/hpc_tools/benchpro/modulefiles
    * - Stampede2
      - /scratch/hpc_tools/benchpro/modulefiles
    * - Lonestar6
      - /scratch/projects/benchpro/modulefiles
    * - Longhorn
      - TBD

Load the BenchPRO site package using the appropriate system path above, this module adds BenchPRO to PYTHONPATH and sets up your environment.

.. code-block::

    ml python3
    ml use [module_path]
    ml benchpro

Next, you need to run a validation process install some user files into $HOME/benchpro, confirm that your system, environment and directory structures are correctly configured before using BenchPRO for the first time. Run the setup with:

.. code-block::

    benchpro --validate

Print help & version information:

.. code-block::

    benchpro --help
    benchpro --version

Display some useful defaults

.. code-block::

    benchpro --defaults

BenchPRO is now setup and ready to use.
