==============
New User Guide
==============

This section describes how to use BenchPRO and its features to automate your benchmarking process. To get started fast, refer to the :ref:`Quick Start <quickstart>` guide.


.. note::

   This guide uses long format input arguments for context, corresponding short format arguments are described :ref:`here <arguments>`.


Terminology
-----------

| Application: a program or set of programs compiled and used to execute benchmark workloads.  
| Benchmark: a specific workload/simulation/dataset used to produce a figure of merit. Typically has an application dependency. 
| Task: a execution instance (via the scheduler or locally on the node) of a compilation or benchmark run.  
| Template file: a shell script with some variables declared.  
| Config file: contains a set of variable key-value pairs used to populate the template.  
| Profile: an application or benchmark available within BenchPRO (i.e. a config & corresponding template file pair)  
| Overload: the act of replacing a default setting or variable with a another one.  

Compile an Application
----------------------

This section will walk you through installing the LAMMPS application (it compiles faster than most other codes) onto Frontera. This guide should also work on other TACC systems.

First, examine all the pre-configured example application and benchmark profiles currently provided by BenchPRO with

.. code-block::

    benchpro --avail 

Install the LAMMPS application with

.. code-block::

    benchpro --build lammps

List applications currently installed

.. code-block::

    benchpro --listApps

You should see that the status of LAMMPS is :code:`DRY RUN`, this is because dry run mode is enabled by default (:code:`dry_run=True`). Therefore BenchPRO generated a LAMMPS compilation script but did not submit the job to the scheduler. This is useful for testing and troubleshooting a workflow without impacting the system scheduler. You can obtain more information about your LAMMPS build with:

.. code-block::

    benchpro --queryApp lammps

Pertenant information is shown here, you can also examine the build script (by default named :code:`job.qsub`) located in the :code:`path` directory. You can submit this LAMMPS compilation script to the scheduler manually, or

Remove the existing dry_run version of LAMMPS with

.. code-block::

    benchpro --delApp lammps

Overload the default 'dry_run' value and rebuild LAMMPS with

.. code-block::
    benchpro --build lammps --overload dry_run=False

Check the details and status of your LAMMPS compilation again with

.. code-block::

    benchpro --queryApp lammps

In this example, parameters in :code:`$BPS_INC/build/config/frontera/lammps.cfg` were used to populate the template script :code:`$BPS_INC/build/template/lammps.template` and produce a job script within a hierachical directory structure under :code:`$BP_APPS` ($SCRATCH/benchpro by default). Parameters for the scheduler, system architecture and compile time optimizations, as well as a module file, were all automatically generated. You can load your LAMMPS module manually with :code:`ml frontera/.../lammps`. Each application built with BenchPRO has a build report generated in order to preserve compilation metadata. BenchPRO uses the module file and build report whenever this application is used to execute a benchmark. You can manually examine LAMMPS's build report located in the build directory or by using the :code:`--queryApp` argument.

Execute a Benchmark
-------------------

We can now run a benchmark with our LAMMPS installation. 

.. note::

    There is no need to wait for the LAMMPS compilation job to complete, BenchPRO is able create scheduler job dependencies between tasks as required (i.e. the benchmark job will depend on the successful completion of the compilation job). In fact, if the setting :code:`build_if_missing=True`, BenchPRO would detect that LAMMPS was not available for the current system when attempting to run a benchmark and build it automatically without us doing the steps above. The process to run a benchmark is similar to application compilation; a configation file is used to populate a template script. A benchmark run is specified with :code:`--bench / -B`. Once again you can check for available benchmarks with the :code:`--avail` argument.

Permenantly disable the dry run mode with :code:`bps dry_run=False` so that we don't have to overload manually overload the setting on the command line. Refer to the :ref:`Changing settings <settings>` section for more information.

Execute the Lennard-Jones benchmark for LAMMPS with

.. code-block::

    benchpro --bench ljmelt

Check the benchmark report with

.. code-block::

    benchpro --queryResult ljmelt

As this benchmark was the most recent BenchPRO job executed, you can use a useful shortcut to check this report

.. code-block::

    benchpro --last

.. note::

    In this example, parameters in :code:`$BPS_INC/bench/config/lammps_ljmelt.cfg` were used to populate the template :code:`$BPS_INC/bench/template/lammps.template`. Much like the application build process, a benchmark report was generated to store metadata associated with this run. It is stored in the benchmark working directory and will be used in the next step to capture the result to the database.

Capture Benchmark Result
------------------------

.. note::
   
   A BenchPRO result is considered to be in one of four states, 'pending', 'complete', 'failed' or 'captured'. The benchmark result will remain on the local system until it has been captured to the database, at which time its state is updated to :code:`captured` or :code:`failed`.

Once the benchmark job has completed, capture results to the database with:

.. code-block::

    benchpro --capture

.. note::

    Your unique instance of LAMMPS was recently compiled and not present in the database, therefore it is also captured to the database automatically.

Display the status of all benchmark runs with

.. code-block::

    benchpro --listResults

Query the results database with

.. code-block::

    benchpro --dbList
    
You can print an abridged report of your benchmark with

.. code-block::
   benchpro --dbResult [jobid]

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



