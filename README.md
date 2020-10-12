# bench-framework
This is a framework to automate and standardize application benchmarking on large scale HPC systems.

Currently there are 5 application profiles available for debugging and testing:
   - LAMMPS-3Mar20
   - OpenFOAM-v2006
   - Quantum Espresso-6.5
   - SWIFTsim-0.8.5
   - WRF-4.2

## Getting Started

The following steps should produce a small scale LAMMPS benchmark. Tested on Stampede2 and Frontera.

### Building an application

1 Download and setup env: 

```
git clone https://gitlab.tacc.utexas.edu/mcawood/bench-framework
cd bench-framework
source sourceme
```
2 List input options:
```
benchtool --help
```
3 List applications available to install:
```
benchtool --avail
```
4 Install a new application:
```
benchtool --build lammps
```
5 List applications currently installed:
```
benchtool --installed
```
By default `dry_run=True` in `settings.cfg` so the build script was created but not submitted to the scheduler. You could submit the job manually, or


6 Remove the dry_run build:
```
benchtool --remove lammps
```
7 Rerun with: 
```
benchtool --install lammps --var dry_run=False
```
8 Check the build report for your application:
```
benchtool --queryApp lammps
```

In this example, parameters in `config/build/lammps-3Mar20_build.cfg` was used to populate the template `templates/build/lammps-3Mar20.build`

### Running a benchmark

The benchmark process is similar to building; a config file is used to populate a template.
A benchmark .cfg file can be provided with the `--param`, if no input is provided, the default cfg file will be used, located in `config/bench/`  

1 Run the LAMMPS benchmark with: 
```
benchtool --bench lammps
```
2 Check result report
```
benchtool --queryResult lammps
```
In this example, parameters in `config/bench/lammps_bench.cfg` as to populate the template `templates/bench/lammps-3Mar20.bench`

### Capture benchmark results

1 List results
```
benchtool --listResults all
```
2 Capture result to database
```
benchtool --capture
```
## Building a new application
benchtool requires two input files to build an application: a config file containing contextualization parameters, and a build template file which will be populated with these parameters. 

You can define as many additional parameters as needed for your application. Eg: additional modules, build options etc. All parameter [label] defined here will be used to fill <<<[label]>>> variables in the template file, thus consistent naming is important.
This file must be located in `configs/build`, with the naming scheme `[code]_build.cfg`

### 2. Build template file

This file is the template for the scheduler job script which will compile the application.
Variables are defined with `<<<[label]>>>` and populated with the variables defined in the config file above.
The label in the template must match the label used in the config file.  
You are able to make use of the `benchmark_repo` variable defined in `settings.cfg` to copy local files. 
This file must be located in `templates/build`, with the naming scheme `[code]-[version].build` 

### 3. Module template file (optional)

You can define you own Lua module template, otherwise a generic one will be created for you.
This file must be located in `templates/build`, with the naming scheme `[code]-[version].module` 

## Running a new application benchmark

The process of setting up an application benchmark is much the same as the build process; a config file is used to populate a job template. 


Any additional parameters may be defined in order to setup the benchmark, i.e dataset label, problem size variables etc.
This file must be located in `configs/runs`, with the naming scheme `[code]_run.cfg`

### 2. Run template file  

As with the build template. this file is populated with the parameters defined in the config file above. This file should include setup of the dataset, any required pre-processing or domain decomposition steps if required, and the appropriate `ibrun` command.
You are able to make use of the `benchmark_repo` variable defined in `settings.cfg` to copy local files. 

This file must be located in `templates/bench`, with the naming scheme `[code]-[version].run` 


# Inputs & settings format

## Command line arguments

| Argument                                              | Description                                                   |
|-------------------------------------------------------|---------------------------------------------------------------|
| --help                                                | Print usage info.                                             |
| --validate                                            | Confirm the installation is correctly configured.             |
| --clean                                               | Remove logs and other temp files left after an execption.     |
| --avail                                               | Print the available application and benchmark profiles.       |
| --build [LABEL]                                       | Compile an available application.                             |
| --installed                                           | Print a list of currently installed applications.             |
| --queryApp [LABEL]                                    | Print compilation information for an installed app.           |
| --remove [LABEL]                                      | Remove application installation matching inpout.              |
| --bench [LABEL]                                       | Run a benchmark.                                              |
| --sched [LABEL]                                       | Use with '--build' or '--bench' to specify a custom scheduler config file instead of the system default. |
| --listResults [all/running/pending/captured/failed]   | List all benchmark results in requested state.                |
| --queryResult [LABEL]                                 | Print config and result of a benchmark run.                   |
| --capture                                             | Validate and capture all pending results to the database.     |
| --queryDB [all/LIST]                                  | Display either all results from DB or results matching colon delimited search list, eg "username=mcawood:code=lammps". |
| --removeResult [all/captured/failed/LABEL]            | Remove local benchmark results matching input criteria.       |
| --overload [LIST]                                     | Replace options in settings.ini or any config file, acceptes a colon delimited list. |

## Global settings
Global settings are defined in the file `settings.ini`

| Label             | Default                       | Description                                                                       |
|-------------------|-------------------------------|-----------------------------------------------------------------------------------|
| **[common]**      |                               | -                                                                                 |
| dry_run           | True                          | Generates job script but does not submit it, useful for testing                   |
| timeout           | 5                             | Delay in seconds after warning and before file deletion event                     |
| sl                | /                             | Filesystem separator.                                                             |
| system_env        | $TACC_SYSTEM                  | Environment variable contained system label (eg: stampede2)                       |
| sched_mpi         | ibrun                         | MPI launcher to use in job script                                                 |
| local_mpi         | mpirun                        | MPI launcher to use on local machine                                              |
| tree_depth        | 6                             | Determines depth of app installation tree.                                        |
| topdir_env_var    | $BENCHTOOL                    | benchtool's working directory environment variable (exported in from sourceme).   |
| log_dir           | ./log                         | Log file directory.                                                               |
| script_basedir    | ./scripts                     | Result validation and system check script directory.                              |
| ssh_key_dir       | ./auth                        | Directory containing SSH keys for server access.                                  |
| mpi_blacklist     | login,staff                   | Hostnames containing these strings are forbidden from executing MPI code.         |
| **[config]**      |                               | -                                                                                 |
| config_basedir    | ./config                      | Top directory for config files.                                                   |
| build_cfg_dir     | build                         | Build config file subdirectory.                                                   |
| bench_cfg_dir     | bench                         | Benchmark config file subdirectory.                                               |
| sched_cfg_dir     | sched                         | Scheduler config file subdirectory.                                               |
| system_cfg_file   | system.cfg                    | File containing system default architecture and core count.                       |
| arch_cfg_file     | architecture_defaults.cfg     | File containing default compile optimization flags.                               |
| compile_cfg_file  | compiler.cfg                  | File containing compiler environment variables.                                   |
| **[templates]**   |                               | -                                                                                 |
| exit_on_missing   | True                          | Exit if template is not fully populates (missing parameters found).               |
| template_basedir  | ./templates                   | Top directory for template files.                                                 |
| build_tmpl_dir    | build                         | Build template file subdirectory.                                                 |
| sched_tmpl_dir    | sched                         | Scheduler template file subdirectory.                                             |
| bench_tmpl_dir    | bench                         | Benchmark template file subdirectory.                                             |
| compile_tmpl_file | compiler.template             | Template for setting environment variables.                                       |
| **[builder]**     |                               | -                                                                                 |
| overwrite         | False                         | If existing installation  is found in build path, replace it.                     |
| build_mode        | sched                         | Accepts 'sched' or 'local', applications compiled via sched job or local shell.   |
| build_basedir     | ./build                       | Top directory for application installation tree.                                  |
| build_subdir      | build                         | Application subdirectory for build files.                                         |
| install_subdir    | install                       | Application subdirectory for installation (--prefix).                             |
| build_log_file    | build                         | Label for build log.                                                              |
| build_report_file | build_report.txt              | Application build report file name.                                               |
| max_build_jobs    | 5                             | Maximum number of concurrent running build jobs allowed in the scheduler.         |
| **[bencher]**     |                               |                                                                                   |
| bench_mode        | sched                         | Accepts 'sched' or 'local', benchmarks run via sched job or local shell.          |
| build_if_missing  | True                          | If application needed for benchmark is not currently installed, install it.       |
| benchmark_repo    | /scratch/06280/mcawood/benchmark_repo  | Directory containing benchmark datasets.                                 |
| bench_basedir     | ./results                     | Top directory containing bechmark runs.                                           |
| bench_log_file    | bench                         | Label for run log.                                                                |
| bench_report_file | bench_report.txt              | Benchmark report file.                                                            |
| output_file       | output.log                    | File name for benchmark stdout.                                                   |
| **[suites]**      |                               |                                                                                   |
| test_suite        | ljmelt,ausurf                 | Exmaple benchmark suite containing a LAMMPS and QE problem set.                   |
| **[results]**     |                               |                                                                                   |
| result_scripts_dir| results                       | Subdirectory inside [script_basedir] containing result validation scripts.        |
| results_log_file  | capture                       | Label for capture log.                                                            |
| **[database]**    |                               |                                                                                   |
| db_host           | tacc-stats03.tacc.utexas.edu  | Database host address.                                                            |
| db_name           | bench_db                      | Database name.                                                                    |
| db_user           | postgres                      | Database user.                                                                    |
| db_passwd         | postgres                      | Datanase user password.                                                           |
| table_name        | results_result                | Postgres table name.                                                              |
| file_copy_handler | scp                           | File transfer method, only scp working currently.                                 |
| ssh_user          | mcawood                       | Username for SSH access to database host.                                         |
| ssh_key           | id_rsa                        | SSH key filename (stored in ./auth)                                               |
| django_static_dir | /home/mcawood/benchdb/static  | Directory for Django static directory (destination for file copies).              |
| **[system]**      |                               | -                                                                                 |
| system_scripts_dir| system                        | Subdirectory in which hardware info collection tools are located.                 |
| system_utils_dir  | hw_utils                      |                                                                                   |

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
| **[result]**          |            |                                                                                  |
| description           | N          | Result explanation/description.                                                  |
| method                | Y          | Results extraction method. Currently 'expr' or 'script' modes supported.         |
| expr                  | Depends    | Required if 'method=expr'. Expression for result extraction (Eg: "grep 'Performance' <file> | cut -d ' ' -f 2")"|
| script                | Depends    | Required if 'method=script'. Filename of script for result extraction.           |
| unit                  | Y          | Result units.                                                                    |


## Directory structure

| Directory         | Purpse                                                    |
|-------------------|-----------------------------------------------------------|
| ./auth            | SSH keys.                                                 |
| ./build           | Application build basedir.                                |
| ./config          | config files containing template parameters.              |
| ./dev             | Contains unit tests etc.                                  |
| ./hw_reporting    | hardware state reporting tools.                           |
| ./log             | Build, bench and catpure log files.                       |
| ./results         | Benchmark result basedir.                                 |
| ./scripts         | Hardware collection and result validation scripts         |
| ./src             | contains Python files and hardware collection bash script.| 
| ./templates       | job template files                                        |
