==============
New User Guide
==============

This guide explains how to use BenchPRO to build one of the provided applications, run a benchmark and capture the result. If you have not yet setup BenchPRO for your user account, refer to the :ref:`user_setup` page.


.. note::

   This guide uses long format input arguments for context, corresponding short format arguments are described :ref:`here <arguments>`.

Build an Application
--------------------

This section will walk you through installing the LAMMPS application (it builds faster than most other codes) onto TACC's Frontera system. This guide will work on other systems but certain assumptions need to be made about the environment & architecture where LAMMPS is being compiled to accurately describe the process.

First, examine all the available applications and benchmarks currently provided by BenchPRO with

.. code-block::

    benchpro --avail 

Install the LAMMPS application with

.. code-block::

    benchpro --build lammps

List applications currently installed

.. code-block::

    benchpro --listApps

You should see that the status of LAMMPS is :code:`DRY RUN`, this is because by default :code:`dry_run=True` in :code:`$BP_HOME/settings.ini`. Therefore BenchPRO generated a LAMMPS compilation script but did not submit it to the scheduler to execute the build process automatically. This is useful for testing and troubleshooting without impacting the system scheduler. You can obtain more information about your LAMMPS build with:

.. code-block::

    benchpro --queryApp lammps

Examine the generated build script (by default named :code:`build.job`) located in the :code:`build_prefix` directory. You can submit this LAMMPS compilation script to the scheduler manually, or

Remove the existing dry_run build

.. code-block::

    benchpro --delApp lammps

Overload the default 'dry_run' value and rebuild LAMMPS with

.. code-block::
    benchpro --build lammps --overload dry_run=False

Check the details and status of your LAMMPS compilation again with

.. code-block::

    benchpro --queryApp lammps

.. note::

    In this example, parameters in :code:`$BP_HOME/config/build/lammps.cfg` were used to contextualize the build template :code:`$BP_HOME/templates/build/lammps.template` and produce a job script within an Lmod-esque directory structure under :code:`$BP_APPS`. Parameters for the scheduler, system architecture and compile time optimizations, as well as a module file, were all automatically generated. You can load your LAMMPS module manually with :code:`ml frontera/.../lammps`. Each application built with BenchPRO has a build report generated in order to preserve compilation metadata. BenchPRO uses the module file and build report whenever this application is used to execute a benchmark. You can manually examine LAMMPS's build report located in the build directory or by using the :code:`--queryApp` argument.

Execute a Benchmark
-------------------

We can now run a benchmark with our LAMMPS installation. 

.. note::

    There is no need to wait for the LAMMPS compilation job to complete, because BenchPRO is able create scheduler job dependencies between tasks as needed (i.e. the benchmark job will depend on the successful completion of the compilation job). In fact, if :code:`build_if_missing=True` in :code:`$BP_HOME/settings.ini`, BenchPRO would detect that LAMMPS was not available for the current system when attempting to run a benchmark and build it automatically without us doing the steps above. The process to run a benchmark is similar to application compilation; a configation file is used to populate a template script. A benchmark run is specified with :code:`--bench / -B`. The benchmark identifier argument can either refer to a single benchmark or a benchmark 'suite' (i.e collection of benchmarks) defined in :code:`$BP_HOME/suites.ini`. Once again you can check for available benchmarks with the :code:`--avail` argument.

If you haven't already, set :code:`dry_run=False` in :code:`$BP_HOME/settings.ini` so that we don't have to overload manually overload the setting on the command line.

Execute the LAMMPS Lennard-Jones benchmark with

.. code-block::

    benchpro --bench ljmelt

.. note::

    BenchPRO will determine reasonable default values for the current system, including scheduler parameters, from :code:`$BP_HOME/config/system.cfg`. You can overload individual parameters using `--overload`, or specify another scheduler config file with the argument :code:`--sched [FILENAME]`.

Check the benchmark report with

.. code-block::

    benchpro --queryResult ljmelt

As this benchmark was the most recent BenchPRO job executed, you can use a useful shortcut to check this report

.. code-block::

    benchpro --last

.. note::

    In this example, parameters in :code:`$BP_HOME/config/bench/lammps_ljmelt.cfg` were used to contetualize the template :code:`$BP_HOME/templates/bench/lammps.template`. Much like the application build process, a bench report was generated to store metadata associated with this run. It is stored in the benchmark result directory and will be used in the next step to capture the result to the database.

Capture Benchmark Result
------------------------

.. note::
   
   A BenchPRO result is considered to be in a :code:`pending` state until it is capture to the database. The benchmark result will remain on the local system until it has been captured to the database, at which time its state is updated to :code:`captured` or :code:`failed`.

Once the LJMelt benchmark job has completed, capture results to the database with:

.. code-block::

    benchpro --capture

.. note::

    Your LAMMPS application was recently compiled and not present in the database, therefore it is also captured to the database automatically.

Display the status of all benchmark runs with

.. code-block::

    benchpro --listResults

Query the result database with

.. code-block::

    benchpro --dbResult

You can filter your query by providing search criteria,and export the results to a .csv file with

.. code-block::

    benchpro --dbResult username=$USER,system=$TACC_SYSTEM,submit_time=$(date +"%Y-%m-%d") --export

You can also query your LAMMPS application entry in the database using the [APPID] from above

.. code-block::

    benchpro --dbApp [APPID]

Once you are satisfied the benchmark result and its associated files have been uploaded to the database, you can remove the local files with

.. code-block::

    benchpro --delResult captured

Web frontend
------------

The captured applications and benchmark results for the TACC site are available through a web portal at http://benchpro.tacc.utexas.edu/

Useful commands
---------------

You can print the default values of several important BenchPRO settings with

.. code-block::

    benchpro --defaults

It may be useful to review your previous commands. BenchPRO maintains its own history, accessible with

.. code-block::

    benchpro --history

You can remove temp, log, csv, and history files by running

.. code-block::

    benchpro --clean

clean will NOT remove your installed applications, to do that run

.. code-block::

    benchpro --delApp all



