# BenchTool
This is a framework to automate and standardize application compilation, benchmarking and result collection on large scale HPC systems.
There are several application profiles included with benchtool for debugging and testing:

| Applications               | Synthetic Benchmarks     |
|----------------------------|--------------------------|
| AMBER 20                   | HPL                      |
| GROMACS 2020.2             | HPCG                     |
| LAMMPS 3Mar20              | STREAM                   |
| MILC 7.8.1                 | GPCNET                   |
| NAMD 2.14                  |                          |
| OpenFOAM v2012             |                          |
| Quantum Espresso 6.5       |                          |
| SWIFTsim 0.9.0             |                          |
| WRF 4.2                    |                          |
| SpecFEM3D Globe 7.0.2      |                          |

These application profiles have been created with the expectation that corresponding source code and datasets are available in the local repository directory.
New applications are continuously being added.

## Getting Started

The following steps will walk you through the basic usage of benchtool and produce a small LAMMPS LJ-melt benchmark. Tested on Stampede2 and Frontera systems at TACC. The initial site setup is not needed on TACC systems as the tool has already been deployed.

### Site Installation

BenchTool is installed as a Python3 package.

1.b Load system Python3
``` 
ml python3
```

2 Download and install BenchTool package: 
```
git clone https://github.com/TACC/benchtool.git
cd benchtool-package
./install.sh [key]
```
Note: The SSH key provided on the command line is required to access the database server to store provenenace data. BenchTool does not interact with this key at all, but will provide you a line to add to crontabfor periodically scanning user results and pushing them to the database server.

The Python package is now installed, as part of the install process user files were installed into $HOME/benchtool from https://github.com/https://github.com/TACC/benchtoolTACC/benchtool

### User Repo

In order to use BenchTool users need to install a local instance of the configuration and template files into their home directory. For additional information on how to install the user files and BenchTool usage information, refer to the user repository here: https://github.com/TACC/benchtool

### Web frontend

The captured applications and benchmark results are available through a Django frontend, which is currently running on tacc-stats03 port 8001. 

## Advanced Features

BenchTool supports a number of more advanced features which may be of use.

### Overloading parameters

Useful for changing a setting for a onetime use. 
Use `benchtool --setup` to confirm important default params from $BT_HOME/settings.ini
You can overload params from settings.ini and params from  your build/bench config file.
Accepts colon delimited lists.
Exception will be raised if overload param does not match existing key in settings.ini or config file.

Example 1: overload dry_run and build locally rather than via sched:
```
benchtool --build lammps --overload dry_run=False build_mode=local
```

Example 2: run LAMMPS benchmark with modified nodes, ranks and threads:
```
bench --bench ljmelt --overload nodes=16 ranks_per_node=8 threads=6
```

### Input list support

Comma delimited lists of nodes, ranks and threads are supported which can be useful for automating scaling and optimization investigations.
These lists can be specified in the config file, or via the overload feature detailed above.
A list of nodes will be iterated over, and for each, the list of threads and ranks will both be iterated over.
If the single thread and multiple ranks are specified, the same thread value will be used for all ranks, and vice versa. If ranks and threads and both larger than a single value but not equal length, an exception will be raised.

Example 1: Run LAMMPS on 4, 8 and 16 nodes, first using 4 ranks per node with 8 threads each, and then 8 ranks per node using 4 threads each:
```
benchtool --bench ljmelt --overload nodes=4,8,16 ranks_per_node=4,8 threads=8,4
```
From this example, the resulting set of runs would look like:
```
Nodes=  4, ranks= 4, threads= 8 
Nodes=  4, ranks= 8, threads= 4 
Nodes=  8, ranks= 4, threads= 8 
Nodes=  8, ranks= 8, threads= 4 
Nodes= 16, ranks= 4, threads= 8 
Nodes= 16, ranks= 8, threads= 4 
```

### Local build and bench modes

Allows you to run the generated scripts in a shell on the local machine rather than  via the scheduler.
Useful for evaluating hardware which is not integrated into the scheduler.

In settings.ini `build_mode` and `bench_mode` are responsible for selecting this feature. Values `sched` or `local` are accepted, or an exception will be raised. 
You can opt to build locally and run via the scheduler, or vice a versa.

### Benchmarks with no application dependency

Some benchmarks such as synthetics are microbenchmarks do require an application be compiled and module created.
You are able to create a benchmark without any dependency to an application. 
This is done by not specifying any values in the [requirements] section of the benchmark config file.


# Inputs & settings format

## Command line arguments

| Argument                                              | Description                                                   |
|-------------------------------------------------------|---------------------------------------------------------------|
| --help                                                | Print usage info.                                             |
| --validate                                            | Confirm the installation is correctly configured.             |
| --clean                                               | Remove logs and other temp files left after an execption.     |
| --avail                                               | Print the available application and benchmark profiles.       |
| --build [LABEL]                                       | Compile an available application.                             |
| --listApps                                            | Print a list of currently installed applications.             |
| --queryApp [LABEL]                                    | Print compilation information for an installed app.           |
| --delApp [LABEL]                                      | Remove application installation matching inpout.              |
| --bench [LABEL]                                       | Run a benchmark.                                              |
| --sched [LABEL]                                       | Use with '--build' or '--bench' to specify a custom scheduler config file instead of the system default. |
| --listResults [all/running/pending/captured/failed]   | List all benchmark results in requested state.                |
| --queryResult [LABEL]                                 | Print config and result of a benchmark run.                   |
| --capture                                             | Validate and capture all pending results to the database.     |
| --dbResult [all/LIST]                                 | Display either all results from DB or results matching colon delimited search list, eg "username=mcawood:code=lammps". |
| --dbApp [APPID]                                       | Display application details                                   |
| --delResult [all/captured/failed/LABEL]               | Remove local benchmark results matching input criteria.       |
| --overload [LIST]                                     | Replace options in settings.ini or any config file, acceptes a colon delimited list. |

## Global settings
Global settings are defined in the file `settings.ini`

| Label             | Default                       | Description                                                                       |
|-------------------|-------------------------------|-----------------------------------------------------------------------------------|
| **[paths]**       |                               | -                                                                                 |
| install_dir       |                               | Populated by installer                                                            |
| build_dir         |                               | Populated by installer                                                            |
| bench_dir         |                               | Populated by installer                                                            |
| **[common]**      |                               | -                                                                                 |
| dry_run           | True                          | Generates job script but does not submit it, useful for testing                   |
| debug             | True                          | Prints additional nonessential messages                                           |
| timeout           | 5                             | Delay in seconds after warning and before file deletion event                     |
| sl                | /                             | Filesystem separator                                                              |
| system_env        | $TACC_SYSTEM                  | Environment variable contained system label (eg: stampede2)                       |
| sched_mpi         | ibrun                         | MPI launcher to use in job script                                                 |
| local_mpi         | mpirun                        | MPI launcher to use on local machine                                              |
| tree_depth        | 6                             | Determines depth of app installation tree                                         |
| topdir_env_var    | $BT_HOME                   | BenchTool's working directory environment variable (exported in from sourceme)    |
| log_dir           | ./log                         | Log file directory                                                                |
| script_basedir    | ./scripts                     | Result validation and system check script directory                               |
| ssh_key_dir       | ./auth                        | Directory containing SSH keys for server access                                   |
| mpi_blacklist     | login,staff                   | Hostnames containing these strings are forbidden from executing MPI code          |
| **[config]**      |                               | -                                                                                 |
| config_basedir    | ./config                      | Top directory for config files                                                    |
| build_cfg_dir     | build                         | Build config file subdirectory                                                    |
| bench_cfg_dir     | bench                         | Benchmark config file subdirectory                                                |
| sched_cfg_dir     | sched                         | Scheduler config file subdirectory                                                |
| system_cfg_file   | system.cfg                    | File containing system default architecture and core count                        |
| arch_cfg_file     | architecture_defaults.cfg     | File containing default compile optimization flags                                |
| compile_cfg_file  | compiler.cfg                  | File containing compiler environment variables                                    |
| **[templates]**   |                               | -                                                                                 |
| exit_on_missing   | True                          | Exit if template is not fully populates (missing parameters found)                |
| template_basedir  | ./templates                   | Top directory for template files                                                  |
| build_tmpl_dir    | build                         | Build template file subdirectory                                                  |
| sched_tmpl_dir    | sched                         | Scheduler template file subdirectory                                              |
| bench_tmpl_dir    | bench                         | Benchmark template file subdirectory                                              |
| compile_tmpl_file | compiler.template             | Template for setting environment variables                                        |
| **[builder]**     |                               | -                                                                                 |
| app_env_var       | $BT_APPS                      | Application directory environment variable                                        |
| overwrite         | False                         | If existing installation  is found in build path, replace it                      |
| build_mode        | sched                         | Accepts 'sched' or 'local', applications compiled via sched job or local shell    |
| build_basedir     | ./build                       | Top directory for application installation tree                                   |
| build_subdir      | build                         | Application subdirectory for build files                                          |
| install_subdir    | install                       | Application subdirectory for installation (--prefix)                              |
| build_log_file    | build                         | Label for build log                                                               |
| build_report_file | build_report.txt              | Application build report file name                                                |
| max_build_jobs    | 5                             | Maximum number of concurrent running build jobs allowed in the scheduler          |
| **[bencher]**     |                               |                                                                                   |
| result_env_var    | $BT_RESULTS                   | Application directory environment variable                                        |
| bench_mode        | sched                         | Accepts 'sched' or 'local', benchmarks run via sched job or local shell           |
| build_if_missing  | True                          | If application needed for benchmark is not currently installed, install it        |
| local_repo    | /scratch/06280/mcawood/local_repo  | Directory containing benchmark datasets                                          |
| bench_basedir     | ./results                     | Top directory containing bechmark runs                                            |
| bench_log_file    | bench                         | Label for run log                                                                 |
| bench_report_file | bench_report.txt              | Benchmark report file                                                             |
| output_file       | output.log                    | File name for benchmark stdout                                                    |
| **[results]**     |                               |                                                                                   |
| move_failed_result| True                          | Move failed results to subdir                                                     |
| result_scripts_dir| results                       | Subdirectory inside [script_basedir] containing result validation scripts         |
| results_log_file  | capture                       | Label for capture log                                                             |
| pending_subdir    | pending                       | Subdirectory for pending results                                                  |
| captured_subdir   | captured                      | Subdirectory for captured results                                                 |
| failed_subdir     | failed                        | Subdirectory for failed results                                                   |
| **[database]**    |                               |                                                                                   |
| db_host           | tacc-stats03.tacc.utexas.edu  | Database host address                                                             |
| db_name           | bench_db                      | Database name                                                                     |
| db_user           | postgres                      | Database user                                                                     |
| db_passwd         | postgres                      | Datanase user password                                                            |
| result_table      | results_result                | Postgres results table name                                                       |
| app_table         | results_application           | Django application table name                                                     |
| file_copy_handler | scp                           | File transfer method, only scp working currently                                  |
| ssh_user          | mcawood                       | Username for SSH access to database host                                          |
| ssh_key           | id_rsa                        | SSH key filename (stored in ./auth)                                               |
| django_static_dir | /home/mcawood/benchdb/static  | Directory for Django static directory (destination for file copies)               |
| **[system]**      |                               | -                                                                                 |
| system_scripts_dir| system                        | Subdirectory in which hardware info collection tools are located                  |
| system_utils_dir  | hw_utils                      |                                                                                   |
| **[suites]**      |                               |                                                                                   |
| [Suite label]     | [list of apps/benchmarks]     | Several example included for 

## Application config files
These config files contain parameters used to populate the application build template file, config files are broken in sections corresponding to general settings, system modules and configuration parameters.

| Label             | Required? | Description                                                                      |
|-------------------|-----------|----------------------------------------------------------------------------------|
| **[general]**     |           |                                                                                  |
| code              | Y         | Application identifier.                                                          |
| version           | Y         | Application version label, accepts x.x, x-x, or strings like 'stable'.           |
| system            | N         | TACC system identifier, if left blank will use $TACC_SYSTEM.                     |
| build_prefix      | N         | Custom build (outside of default tree).                                          |
| build_template    | N         | Overwrite default build template file.                                           | 
| **[modules]**     |           | NOTE: user may add as many custom fields to this section as needed.              |
| compiler          | Y         | Module name of compile, eg: 'intel/18.0.2' or just 'intel' for LMod default.     |
| mpi               | Y         | Module name of MPI, eg: 'impi/18.0.2' or just 'impi' for LMod default.           |
| **[config]**      |           | NOTE: user may add as many fields to this section as needed.                     |
| arch              | N         | Generates architecture specific optimization flags. If left blank will use system default, set to 'system' to combine with 'opt_flags' below  | 
| opt_flags         | N         | Used to add additional optimization flags, eg: '-g -ipo'  etc.  If arch is not set, this will be only optimization flags used.        |
| build_label       | N         | Custom build label, replaces arch default eg: skylake-xeon. Required if 'opt_flags' is set and 'arch' is not                 |
| bin_dir           | N         | Set bin dir suffix to add executable to PATH, eg: bin, run etc.                  | 
| exe               | Y         | Name of application executable, used to check compilation was successful.        |
| collect_hw_stats  | N         | Runs the hardware stats collection tool after build.                             |

## Benchmark config file
These config files contain parameters used to populate the benchmark template script. The file structure is:

| Label                 | Required?  | Description                                                                      |
|-----------------------|------------|----------------------------------------------------------------------------------|
| **[requirements]**    |            | NOTE: user may add as many fields to this section as needed.                     |
| code                  | N          | This benchmark requires an installed application matching code=""                |
| version               | N          | This benchmark requires an installed application matching version=""             |
| label                 | N          | This benchmark requires an installed application matching label=""               |
| **[runtime]**         |            |                                                                                  |
| nodes                 | Y          | Number of nodes on which to run, accepts comma-delimited list.                   |
| ranks_per_node        | N          | MPI ranks per node.                                                              |
| threads               | Y          | Threads per MPI rank.                                                            |
| max_running_jobs      | N          | Sets maximum number of concurrent running scheduler jobs.                        |
| hostlist              | Depends    | Either hostlist or hostfile required if benchmarking on local system (no sched). |
| hostfile              | Depends    |                                                                                  |    
| **[config]**          |            | NOTE: user may add as many fields to this section as needed.                     |
| label                 | Depends    | Required if this benchmark has no application dependency.                        | 
| exe                   | Y          | Application executable.                                                          |
| dataset               | Y          | Benchmark dataset label.                                                         |
| collect_hw_stats      | N          | Run hardware info collection after benchmark.                                    |
| output_file           | N          | File to redirect stdout, if empty will use stdout for sched jobs, or 'output_file' from settings.ini for local job.  | 
| **[result]**          |            |                                                                                  |
| description           | N          | Result explanation/description.                                                  |
| method                | Y          | Results extraction method. Currently 'expr' or 'script' modes supported.         |
| expr                  | Depends    | Required if 'method=expr'. Expression for result extraction (Eg: "grep 'Performance' <file> | cut -d ' ' -f 2")"|
| script                | Depends    | Required if 'method=script'. Filename of script for result extraction.           |
| unit                  | Y          | Result units.                                                                    |


## Directory structure

| Directory         | Purpse                                                    |
|-------------------|-----------------------------------------------------------|
| $BT_HOME/auth            | SSH keys.                                                 |
| $BT_APPS                 | Application build basedir.                                |
| $BT_HOME/config          | config files containing template parameters.              |
| $BT_HOME/dev             | Contains unit tests etc.                                  |
| $BT_HOME/doc             | Contains Sphinx generated documentation. WIP              |
| $BT_HOME/log             | Build, bench and catpure log files.                       |
| $BT_HOME/resources       | Contains useful content including modulefiles, hardware collection and result validation scripts.    |
| $BT_RESULTS              | Benchmark result basedir.                                 |
| $BT_HOME/templates       | job template files                                        |
