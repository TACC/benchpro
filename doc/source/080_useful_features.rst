=================
Advanced Features
=================

BenchPRO supports a number of additional features which may be of use.

Overloading parameters
----------------------

Useful for changing a setting for a onetime use. 
Use `benchpro --setup` to confirm important default params from $BP_HOME/settings.ini
You can overload any of the default parameters read from file with the `-o`/`--overload` flag. 
Parameters are overloaded with a list of key-value pairs, or by provided a filename with overloads defined.
An exception will be raised if a provided overload key does not match an existing parameter read from file.

Example 1: overload dry_run and build locally rather than via sched:

.. code-block::

    benchpro -b lammps --overload dry_run=False build_mode=local

Example 2: run LAMMPS benchmark with modified nodes, ranks and threads:

.. code-block::

    benchpro -B ljmelt --overload nodes=16 ranks_per_node=8 threads=6

Example 3: run a collection of benchmarks across a range of hardware, allowing only 1 active task at a time:

.. code-block::

    vim layout.txt
    > nodes = 16,32,64
    > ranks_per_node=2
    > threads=28

    benchpro -B ljmelt gromacs_stmv new_conus12km --overload layout.txt max_running_jobs=1

Input list support
------------------

Comma delimited lists of nodes, ranks and threads are supported which can be useful for automating scaling and optimization investigations.
These lists can be specified in the config file, or via the overload feature detailed above.
A list of nodes will be iterated over, and for each, the list of threads and ranks will both be iterated over.
If the single thread and multiple ranks are specified, the same thread value will be used for all ranks, and vice versa. If ranks and threads and both larger than a single value but not equal length, an exception will be raised.

Example 1: Run LAMMPS on 4, 8 and 16 nodes, first using 4 ranks per node with 8 threads each, and then 8 ranks per node using 4 threads each:

.. code-block::

    benchpro --bench ljmelt --overload nodes=4,8,16 ranks_per_node=4,8 threads=8,4

From this example, the resulting set of runs would look like:

.. code-block::

    Nodes=  4, ranks= 4, threads= 8 
    Nodes=  4, ranks= 8, threads= 4 
    Nodes=  8, ranks= 4, threads= 8 
    Nodes=  8, ranks= 8, threads= 4 
    Nodes= 16, ranks= 4, threads= 8 
    Nodes= 16, ranks= 8, threads= 4 

Local build and bench modes
---------------------------

Allows you to run the generated scripts in a shell on the local machine rather than  via the scheduler.
Useful for evaluating hardware which is not integrated into the scheduler.

In settings.ini `build_mode` and `bench_mode` are responsible for selecting this feature. Values `sched` or `local` are accepted, or an exception will be raised. 
You can opt to build locally and run via the scheduler, or vice a versa.

Benchmarks with no application dependency
-----------------------------------------

Some benchmarks such as synthetics are microbenchmarks do require an application be compiled and module created.
You are able to create a benchmark without any dependency to an application. 
This is done by not specifying any values in the [requirements] section of the benchmark config file.

