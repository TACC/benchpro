===============
Useful Features
===============

BenchPRO supports a number of additional features which may be of use.

Changing settings
-----------------

.. _setting:

BenchPRO supports several mechanisms for modifying default settings. These settings can control BenchPRO functionality or any parameters associated with your application or benchmarking process.

1. One-Time, via commandline argument

To temporarily modify these parameters for a single run, the :code:`-o / --overload` argument is available.   

Example: enable dry_run mode to test modifications to your benchmark script:

.. code-block::

    benchpro -b lammps --overload dry_run=True

Example: run LAMMPS benchmark with modified runtime parameters:

.. code-block::

    benchpro -B ljmelt --overload nodes=16 ranks_per_node=8 threads=6

Example: run a collection of benchmarks across a range of hardware, allowing only 1 active task at a time:

.. code-block::

    vim layout.txt
    > nodes = 16,32,64
    > ranks_per_node=2
    > threads=28

    benchpro -B ljmelt gromacs_stmv new_conus12km --overload layout.txt max_running_jobs=1

2. Profile specific, via configuration file

The compilation/benchmark config files support parameter overloading, which is applied only to that profile. 

.. code-block::

    [overload]
    sync_staging = True
    build_mode = local

The above example enforces synchronous file staging as well as execution on the local node via a subshell, rather than submitted to the scheduler. These overloads are only applied to this specific profile.

3. Permentantly, via user.ini

You are able to permenantly modify defaults. Do this by adding key-value pairs to :code:`$BP_HOME/user.ini`. These parameters will be applied to every task BenchPRO executes. To simplify interacting with this overloads, use the BenchPRO Setter (:code:`bps`) utility.

Example

.. code-block::
    
    bps dry_run=False


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

In user.ini `build_mode` and `bench_mode` are responsible for selecting this feature. Values `sched` or `local` are accepted, or an exception will be raised. 
You can opt to build locally and run via the scheduler, or vice a versa.

Benchmarks with no application dependency
-----------------------------------------

Some benchmarks such as synthetics are microbenchmarks do require an application be compiled and module created.
You are able to create a benchmark without any dependency to an application. 
This is done by not specifying any values in the [requirements] section of the benchmark config file.

