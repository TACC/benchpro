==========================
Integrating your Benchmark
==========================

The process of setting up an application benchmark is much the same as the build process; a config file is used to populate a benchmark template.

Benchmark config file
---------------------

The configuration files used for running benchmarks contains the following fields:

+-----------------------+------------+----------------------------------------------------------------------------------+
| Label                 | Required?  | Description                                                                      |
+=======================+============+==================================================================================+
| **[requirements]**    |       NOTE: user may add as many fields to this section as needed.                            |
+-----------------------+------------+----------------------------------------------------------------------------------+
| code                  | N          | This benchmark requires an installed application matching code=""                |
+-----------------------+------------+----------------------------------------------------------------------------------+
| version               | N          | This benchmark requires an installed application matching version=""             |
+-----------------------+------------+----------------------------------------------------------------------------------+
| build_label           | N          | This benchmark requires an installed application matching build_label=""         |
+-----------------------+------------+----------------------------------------------------------------------------------+
| system                | N          | This benchmark requires an installed application matching system=""              |
+-----------------------+------------+----------------------------------------------------------------------------------+
| **[runtime]**                                                                                                         |
+-----------------------+------------+----------------------------------------------------------------------------------+
| nodes                 | Y          | Number of nodes on which to run, accepts comma-delimited list.                   |
+-----------------------+------------+----------------------------------------------------------------------------------+
| ranks_per_node        | N          | MPI ranks per node, accepts comma-delimited list.                                |
+-----------------------+------------+----------------------------------------------------------------------------------+
| threads               | N          | Threads per MPI rank, accepts comma-delimited list.                              |
+-----------------------+------------+----------------------------------------------------------------------------------+
| gpus                  | N          | Number of GPUs to run on, accepts comma-delimited list.                          |
+-----------------------+------------+----------------------------------------------------------------------------------+
| max_running_jobs      | N          | Sets maximum number of concurrent running scheduler jobs.                        |
+-----------------------+------------+----------------------------------------------------------------------------------+
| hostlist              | Depends    | Either hostlist or hostfile required if on local system (bench_mode=local).      |
+-----------------------+------------+----------------------------------------------------------------------------------+
| hostfile              | Depends    |                                                                                  |
+-----------------------+------------+----------------------------------------------------------------------------------+
| **[config]**          |        NOTE: user may add as many fields to this section as needed.                           |
+-----------------------+------------+----------------------------------------------------------------------------------+
| dataset               | Y          | Benchmark dataset label, used in ID string.                                      |
+-----------------------+------------+----------------------------------------------------------------------------------+
| exe                   | N          | Application executable.                                                          |
+-----------------------+------------+----------------------------------------------------------------------------------+
| bench_label           | N          | Optional naming string.                                                          |
+-----------------------+------------+----------------------------------------------------------------------------------+
| collect_hw_stats      | N          | Run hardware info collection after benchmark.                                    |
+-----------------------+------------+----------------------------------------------------------------------------------+
| script_additions      | N          | File in $BP_HOME/templates to add to benchmark job script.                       |
+-----------------------+------------+----------------------------------------------------------------------------------+
| arch                  | N          | Required architecture for this benchmark, e.g. cuda.                             |
+-----------------------+------------+----------------------------------------------------------------------------------+
| **[result]**                                                                                                          |
+-----------------------+------------+----------------------------------------------------------------------------------+
| description           | N          | Result explanation/description.                                                  |
+-----------------------+------------+----------------------------------------------------------------------------------+
| output_file           | N          | File to redirect stdout, if empty will use stdout for sched jobs, or             |
|                       |            | 'output_file' from user.ini for local job.                                   |
+-----------------------+------------+----------------------------------------------------------------------------------+
| method                | Y          | Results extraction method. Currently 'expr' or 'script' modes supported.         |
+-----------------------+------------+----------------------------------------------------------------------------------+
| expr                  | Depends    | Required if 'method=expr'. Expression for result extraction from file            |
|                       |            | (Eg: "grep 'Performance' <file> | cut -d ' ' -f 2")".                            |
+-----------------------+------------+----------------------------------------------------------------------------------+
| script                | Depends    | Required if 'method=script'. Filename of script for result extraction.           |
+-----------------------+------------+----------------------------------------------------------------------------------+
| unit                  | Y          | Result units.                                                                    |
+-----------------------+------------+----------------------------------------------------------------------------------+


requirements
^^^^^^^^^^^^

where fields are defined to create requirements to an application. More fields produce a finer, more specific application selection criteria.

runtime
^^^^^^^

where job setup parameters are defined.

config
^^^^^^

where bench script parameters are defined.

result
^^^^^^

where result collection parameters are defined.

Any additional parameters may be defined in order to setup the benchmark, i.e dataset label, problem size variables etc.
This file must be located in :code:`$BP_HOME/bench/config`, preferably with the naming scheme :code:`[label].cfg`.

Benchmark template file
-----------------------

As with the build template. The benchmark template file is populated with the parameters defined in the config file above. This file should include setup of the dataset, any required pre-processing or domain decomposition steps if required, and the appropriate mpi_exec command.
You are able to make use of the :code:`local_repo` variable defined in :code:`$BP_HOME/user.ini` to copy local files.

This file must be located in :code:`$BP_HOME/bench/templates`, with the naming scheme :code:`[label].template`.

The benchmark added above would be run with the following command:

.. code-block::
   
    benchpro --bench [dataset]

Note: BenchPRO will attempt to match your benchmark input to a unique config filename. The specificity of the input will depend on the number of similar config files.
It may be helpful to build with :code:`dry_run=True` initially to confirm the build script was generated as expected, before removing and rebuilding with :code:`dry_run=False` to launch the build job.


Example Script
--------------

Below is a benchmark job script generated by BenchPRO. Everything outside the 'USER SECTION' is produced by BenchPRO, which depends on parameters provided in the configuration file, as well as the current system and architecture. 

.. code-block::

    #!/bin/bash
    #SBATCH -J ljmelt
    #SBATCH -o /scratch1/06280/mcawood/benchpro/results/pending/mcawood_ljmelt_2023-06-20T14-01_001N_56R_01T_00G/stdout.log
    #SBATCH -e /scratch1/06280/mcawood/benchpro/results/pending/mcawood_ljmelt_2023-06-20T14-01_001N_56R_01T_00G/stderr.log
    #SBATCH -p small
    #SBATCH -t 00:10:00
    #SBATCH -N 1
    #SBATCH -n 56
    #SBATCH -A A-ccsc
    echo "START `date +"%Y"-%m-%dT%T` `date +"%s"`"

    echo "JobID:    ${SLURM_JOB_ID}"
    echo "User:     ${USER}"
    echo "Hostlist: ${SLURM_NODELIST}"

    export         working_path=/scratch1/06280/mcawood/benchpro/results/pending/mcawood_ljmelt_2023-06-20T14-01_001N_56R_01T_00G
    export          output_file=stdout.log
    export             mpi_exec=ibrun
    export          base_module=/scratch1/06280/mcawood/benchpro/apps/modulefiles
    export           app_module=frontera/cascadelake/intel22/intel22impi/lammps/23Jun2022/default
    export              threads=1
    export                ranks=56
    export                nodes=1
    export                 gpus=0

    # Create working directory
    mkdir -p ${working_path} && cd ${working_path}

    export             template=lammps
    export          bench_label=ljmelt
    export              dataset=ljmelt_4M_per_node_250_steps
    export        collect_stats=True
    export     script_additions=
    export                  exe=lmp_intel_cpu_intelmpi
    export                 arch=
    export           local_repo=/scratch1/06280/mcawood/benchpro/repo
    export               stdout=stdout.log
    export               stderr=stderr.log
    export      OMP_NUM_THREADS=${threads}

    # Load Modules
    ml use /scratch1/hpc_tools/benchpro-dev/modulefiles
    ml use ${base_module}
    ml benchpro
    ml ${app_module}
    ml

    # [files]
    stage https://web.corral.tacc.utexas.edu/ASC23006/datasets/in.ljmelt_4M_per_node_250_steps


    #-------USER SECTION------
    ...
    #-------------------------

    # Provenance data collection script
    $BPS_INC/resources/scripts/stats/collect_stats $BP_RESULTS/pending/mcawood_ljmelt_2023-06-20T14-01_001N_56R_01T_00G/hw_report

    echo "END `date +"%Y"-%m-%dT%T` `date +"%s"`"

