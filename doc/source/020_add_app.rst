=============================
Integrating your Application
=============================

BenchPRO requires two input files (collectively refered to as a 'profile') to build an application: a configuration file containing variables, as well as a template script which will be populated with these variables and executed.


Configuration file
-----------

The configuration files used for compiling application contains the following fields:

+-------------------+-----------+----------------------------------------------------------------------------------+
| Label             | Required? | Description                                                                      |
+-------------------+-----------+----------------------------------------------------------------------------------+
| **[general]**                                                                                                    |
+-------------------+-----------+----------------------------------------------------------------------------------+
| code              | Y         | Application identifier.                                                          |
+-------------------+-----------+----------------------------------------------------------------------------------+
| version           | Y         | Application version label, accepts x.x, x-x, or strings like 'stable'.           |
+-------------------+-----------+----------------------------------------------------------------------------------+
| system            | N         | TACC system identifier, if left blank will use $TACC_SYSTEM.                     |
+-------------------+-----------+----------------------------------------------------------------------------------+
| build_prefix      | N         | Custom build (outside of default tree).                                          |
+-------------------+-----------+----------------------------------------------------------------------------------+
| template          | N         | Overwrite default build template file.                                           |
+-------------------+-----------+----------------------------------------------------------------------------------+
| module_use        | N         | Path to be added to MODULEPATH, for using nonstandard modules.                   |
+-------------------+-----------+----------------------------------------------------------------------------------+
| sched_cfg         | N         | Name of nonstandard scheduler config file to use.                                |
+-------------------+-----------+----------------------------------------------------------------------------------+
| **[modules]**     |          NOTE: user may add as many custom fields to this section as needed.                 |
+-------------------+-----------+----------------------------------------------------------------------------------+
| compiler          | Y         | Module name of compiler, eg: 'intel/18.0.2' or just 'intel' for default.         |
+-------------------+-----------+----------------------------------------------------------------------------------+
| mpi               | Y         | Module name of MPI, eg: 'impi/18.0.2' or just 'impi' for default.                |
+-------------------+-----------+----------------------------------------------------------------------------------+
| **[config]**      |          NOTE: user may add as many fields to this section as needed.                        |
+-------------------+-----------+----------------------------------------------------------------------------------+
| arch              | N         | Generates architecture specific optimization flags. If left blank will use       |
|                   |           | system default, set to 'system' to combine with 'opt_flags' below                |
+-------------------+-----------+----------------------------------------------------------------------------------+
| opt_flags         | N         | Used to add additional optimization flags, eg: '-g -ipo'  etc.  If arch is not   |
|                   |           |    set, this will be only optimization flags used.                               |
+-------------------+-----------+----------------------------------------------------------------------------------+
| build_label       | N         | Custom build label, replaces arch default eg: skylake-xeon. Required if          |
|                   |           | 'opt_flags' is set and 'arch' is not                                             |
+-------------------+-----------+----------------------------------------------------------------------------------+
| bin_dir           | N         | Path to executable within application directory, eg: bin, run etc.               |
+-------------------+-----------+----------------------------------------------------------------------------------+
| exe               | Y         | Name of application executable, used to check compilation was successful.        |
+-------------------+-----------+----------------------------------------------------------------------------------+
| collect_hw_stats  | N         | Runs the hardware stats collection tool after build.                             |
+-------------------+-----------+----------------------------------------------------------------------------------+
| script_additions  | N         | Filename in $BP_HOME/templates, to be added to build script.                     |
+-------------------+-----------+----------------------------------------------------------------------------------+

general
^^^^^^^
Fields for general application info are provide, such as name and version. You can also specify a custom system label, which limits this application to that specific system (useful for avoiding inadvertantly building the wrong application on a given system). By default BenchPRO will attempt to match this config file with its corresponsing template file using the application name. You can overwrite this default template file by adding the :code:`template` field to this section.

modules
^^^^^^^
The section  :code:`compiler` and :code:`mpi` are required, while more modules can be specified if needed. Every module must be available on the local machine, if you are cross compiling to another platform (e.g. to frontera-rtx) and require system modules not present on the current node, you can set `check_modules=False` in user.ini to bypass this check.

:code:`module_use` can be provided to add a nonstandard path to MODULEPATH

config
^^^^^^
where variables used in the build template script can be added.

additionally, you can define as many additional parameters as needed for your application in this section. Eg: configure flags, build options, etc. All parameters :code:`[param]` defined here will be used to fill :code:`<<<[param]>>>` variables of the same name in the template file, thus consistent naming is important.
This file must be located in :code:`$BP_HOME/build/config`, preferably with the naming scheme :code:`[label].cfg`.

files
^^^^^
This section allows the user to have BenchPRO automatically collect input files for the build process. BenchPRO currently supports :code:`local` and :code:`download` operations. If BenchPRO detects that the local or downloaded file is an archive, it will automatically extract the archive to the correct working directory. BenchPRO will search for local files in the $BP_REPO directory. The format of the file staging section is:

.. code-block::

    local = [list],[of],[files]
    download = [list],[of],[URLs]

This file staging process occurs in 1 of 2 ways, depending on the state of :code:`sync_staging` in :code:`$BP_HOME/user.ini`. BenchPRO will either synchronously copy/download/extract during the script creation process, alternatively the file staging will occur during job execution itself. In either case BenchPRO will confirm that the file or URL specified exists before continuing. 


overload
^^^^^^^^

This section allows you to modify default parameters for this specific application. Refer to :ref:`Changing settings <setting>` for additional information.


Build template file
-------------------

The build template file is used to gerenate a contextualized build script which will executed to compile the application. Variables are defined with :code:`<<<[param]>>>` syntax and populated with the variables defined in the config file above. If a :code:`<<<[param]>>>` in the build template is not successfully populated and :code:`exit_on_missing=True` in :code:`$BP_HOME/user.ini`, BenchPRO will abort the build process. You are able to make use of the :code:`local_repo` variable defined in :code:`$BP_HOME/user.ini` to store and use files locally, if you'd rather manage your input files manually. This file must be located in :code:`$BP_HOME/build/templates`, preferablly with the naming scheme :code:`[code_label].template`.

The contextualized build script generated by BenchPRO will have the format:

.. code-block::

    [scheduler options]
    [job level details]
    [export environment variables]
    [load modules]
    [file staging]
    [user section]
    [executable check]

Module template file (optional)
-------------------------------

It is possible to define your own .lua module template and store it in :code:`$BP_HOME/build/templates` with the naming scheme :code:`[code_label].module`, alternatively BenchPRO will generate a generic module file for you.

The application added above would be built with the following command:

.. code-block::

    benchpro --build [code_label]


Example Script
--------------

Below is an application compilation job script generated by BenchPRO. Everything outside the 'USER SECTION' is produced by BenchPRO, which depends on parameters provided in the configuration file, as well as the current system and architecture.

.. code-block::

    #!/bin/bash
    #SBATCH -J lammps_build
    #SBATCH -o /scratch1/06280/mcawood/benchpro/apps/frontera/cascadelake/intel22/intel22impi/lammps/23Jun2022/default/stdout.log
    #SBATCH -e /scratch1/06280/mcawood/benchpro/apps/frontera/cascadelake/intel22/intel22impi/lammps/23Jun2022/default/stderr.log
    #SBATCH -p small
    #SBATCH -t 01:00:00
    #SBATCH -N 1
    #SBATCH -n 1
    #SBATCH -A A-ccsc
    echo "START `date +"%Y"-%m-%dT%T` `date +"%s"`"

    echo "JobID:    ${SLURM_JOB_ID}"
    echo "User:     ${USER}"
    echo "Hostlist: ${SLURM_NODELIST}"

    export   working_path=/scratch1/06280/mcawood/benchpro/apps/frontera/cascadelake/intel22/intel22impi/lammps/23Jun2022/default/build
    export   install_path=/scratch1/06280/mcawood/benchpro/apps/frontera/cascadelake/intel22/intel22impi/lammps/23Jun2022/default/install
    export     local_repo=/scratch1/06280/mcawood/benchpro/repo
    export        version=23Jun2022
    export      opt_flags='-O2 -xCORE-AVX512 -sox'
    export            exe=lmp_intel_cpu_intelmpi
    export    build_label=default
    export        threads=8

    # Create application directories
    mkdir -p ${install_path}
    mkdir -p ${working_path} && cd ${working_path}

    # [config]
    export                 arch=cascadelake
    export            opt_flags='-O2 -xCORE-AVX512 -sox'
    export          build_label=default
    export              bin_dir=
    export                  exe=lmp_intel_cpu_intelmpi
    export        collect_stats=True
    export     script_additions=
    export           local_repo=/scratch1/06280/mcawood/benchpro/repo
    export                cores=56
    export                nodes=1
    export               stdout=stdout.log
    export               stderr=stderr.log

    # [modules]
    export            compiler=intel/22.1.2
    export                 mpi=intel22/impi/22.1.2

    # Load modules
    ml use /scratch1/hpc_tools/benchpro-dev/modulefiles
    ml use /scratch1/projects/compilers/modulefiles
    ml benchpro
    ml intel/22.1.2
    ml intel22/impi/22.1.2
    ml

    # Stage Files
    stage https://web.corral.tacc.utexas.edu/ASC23006/apps/lammps-23Jun2022.tgz

    # Compiler variables
    export      CC=icc
    export     CXX=icpc
    export      FC=ifort
    export     F77=ifort
    export     F90=ifort
    export   MPICC=mpicc
    export  MPICXX=mpicxx
    export MPIFORT=mpifort

    #------USER SECTION------
    ...
    #------------------------

    ldd ${install_path}/lmp_intel_cpu_intelmpi
    echo "END `date +"%Y"-%m-%dT%T` `date +"%s"`"

