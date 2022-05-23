
![Lmod Logo](https://github.com/TACC/BenchPRO/raw/main/resources/images/benchpro_white.png)


[![Documentation Status](https://readthedocs.org/projects/benchpro/badge/?version=latest)](https://benchpro.readthedocs.io/en/latest/?badge=latest)


# BenchPRO
BenchPRO - Benchmark Performance & Reproducibility Orchestrator, is a framework to automate and standardize application compilation, benchmarking and result collection on large scale HPC systems.

## BenchPRO URLs

- Documentation    https://benchpro.readthedocs.io/en/latest/
- Client Repo      https://github.com/TACC/benchpro
- Site Repo        https://github.com/TACC/benchpro-site
- Database Repo    https://github.com/TACC/benchpro-db


## Getting Started

### Install

The BenchPRO site package should already be installed on most TACC systems. If it is not, contact mcawood@tacc.utexas.edu or install it from the [benchpro-package](https://github.com/TACC/benchpro-package) repository. Assuming the site package is available, you need to install a local copy of the configuration and template files to use BenchPRO.

| System             | Module Path                              |
|--------------------|------------------------------------------|
| Frontera           | /scratch1/hpc_tools/benchpro/modulefiles |
| Stampede2          | /scratch/hpc_tools/benchpro/modulefiles  |
| Lonestar6          | /scratch/projects/benchtool/modulefiles  |
| Longhorn           | TBD                                      |

1 Load the BenchPRO site package using the appropriate system path above, this module adds BenchPRO to PYTHONPATH and sets up your environment.
```
ml python3
ml use [module_path]
ml benchpro
```
2 You will likely get a warning stating you need to install missing user files. Follow the instructions to clone those files from this repository:
```
ml git
git clone https://github.com/TACC/benchpro.git $HOME/benchpro
```
3 Finally, you need to run a validation process to confirm that your system, environment and directory structures are correctly configured before using BenchPRO for the first time. Run this with:
```
benchpro --validate
```
NOTE: Some of the hardware data collection functionality provided by BenchPRO requires root access, you can either run the permissions script below to privilege said scripts, or manage without this data collection feature.
```
sudo -E $BP_HOME/resources/scripts/change_permissions
```
4 Print help & version information:
```
benchpro --help
benchpro --version
```
5 Display some useful defaults 
```
benchpro --defaults
```
These defaults are set by the $BP_HOME/settings.ini 


### Build an Application
This section will walk you through building your first application with BenchPRO using an included application profile.

1 List all available applications and benchmarks with:
```
benchpro -a
```
2 Install LAMMPS:
```
benchpro -b lammps
```
3 List applications currently installed:
```
benchpro -la
```
You will see that LAMMPS is labelled as `DRY RUN` because `dry_run=True` in `$BP_HOME/settings.ini` by default. Therefore BenchPRO generated a LAMMPS compilation script but did not submit it to the scheduler to execute the build process. You can obtain more information about your LAMMPS deployment with:
```
benchpro -qa lammps
```
You can examine the build script `build.batch` located in the `build_prefix` directory. Submit your LAMMPS compilation script to the scheduler manually, or
4 Remove the dry_run build:
```
benchpro -da lammps
```
5 Overload the default 'dry_run' value and rebuild LAMMPS with: 
```
benchpro -b lammps -o dry_run=False
```
6 Now check the details and status of your LAMMPS compilation job with:
```
benchpro -qa lammps
```
In this example, parameters in `$BP_HOME/config/build/lammps.cfg` were used to contextualize the build template `$BP_HOME/templates/build/lammps.template` and produce a job script. Parameters for the job, system architecture, compile time optimizations and a module file were automatically generated. You can load your LAMMPS module with `ml lammps`. For each application that is built, a 'build_report' is generated in order to preserve metadata about the application. This build report is referenced whenever the application is used to run a benchmark, and also when this application is captured to the database. You can manually examine this report in the application directory or by using the `--queryApp / -qa` flag.

### Run a Benchmark

We can now run a benchmark with our LAMMPS installation. There is no need to wait for the LAMMPS build job to complete because BenchPRO is able create job dependencies between tasks when needed. In fact, if `build_if_missing=True` in `$BP_HOME/settings.ini`, BenchPRO would detect that LAMMPS is not installed for the current system when attempting to run a benchmark and build it automatically without us doing the steps above. The process to run a benchmark is similar to compilation; a configation file is used to populate a template script. A benchmark run is specified with `--bench / -B`. The argument may be a single benchmark label, or a benchmark 'suite' (i.e collection of benchmarks) defined in `settings.ini`. Once again you can check for available benchmarks with `--avail / -a`.  

1 If you haven't already, modify `$BP_HOME/settings.ini' to disable the dry_run mode.
```
dry_run = False
```
2 Generate the LAMMPS Lennard-Jones benchmark with: 
```
benchpro -B ljmelt 
```
We changed `settings.ini` so we don't need to use the `--overload / -o` flag to disable the dry_run mode. 
Note that BenchPRO will use the default scheduler parameters for your system from a file defined in `$BP_HOME/config/system.cfg`. You can overload individual parameters using `--overload`, or use another scheduler config file with the flag `--sched [FILENAME]`. 

3 Check the benchmark report with:
```
benchpro -qr ljmelt
```
4 Because this Lennard-Jones benchmark was the last BenchPRO job executed, a useful shortcut is available to check this report:
```
benchpro --last
```

In this example, parameters in `$BP_HOME/config/bench/lammps_ljmelt.cfg` were used to contextualize the template `$BP_HOME/templates/bench/lammps.template`
Much like the build process, a 'bench_report' was generated to store metadata associated with this benchmark run. It is stored in the benchmark result direcotry and will be used in the next step to capture the result to the database.

### Capture Benchmark Result

A benchmark result exists in four states, during scheduler queueing and execution it is considered in `running` state, upon completion it will remain on the local system in a `complete` state, until it is captured it to the database when its state changes to `captured` or `failed`. 

1 We can check on the status of all benchmark runs with:
```
benchpro -lr 
```
2 Once your LAMMPS benchmark result is in the complete state, capture all complete results to the database with:
```
benchpro -C
```
3 You can now query your result in the database with :
```
benchpro --dbResult 
```
4 You can provide search criteria to narrow the results and export these results to a .csv file with:
```
benchpro --dbResult username=$USER system=$TACC_SYSTEM submit_time=$(date +"%Y-%m-%d") --export
```
Because your LAMMPS application was recently compiled and not present in the database, it was added to the application table automatically. An identifier string is generated and assigned to each unique application instance when added to the database, this identifier [APPID] can be used to query the application.

5 Query your application details using the [APPID] displayed from the query in the previous step:
```
benchpro --dbApp [APPID]
```
6 Once you are satisfied the benchmark result and its associated files have been uploaded to the database, you can remove the local copy with:
```
benchpro --delResult captured
```

### Web frontend

The captured applications and benchmark results are available through a web frontend here http://benchpro.tacc.utexas.edu/. 

### Useful commands

You can print the default values of several important parameters with:
```
benchpro --setup
```

It may be useful to review your previous BenchPRO commands, do this with:
```
benchpro --history
```

You can remove tmp, log, csv, and history files by running:
```
benchpro --clean
```

clean will NOT remove your all installed applications, to do that run:
```
benchpro --delApp all
```

## Adding a new Application
BenchPRO requires two input files to build an application: a config file containing contextualization parameters, and a build template file which will be populated with these parameters and executed. 

### 1. Build config file

A full detailed list of config file fields are provided at the bottom of this README. A config file is seperated into the following sections:
 - `[general]` where information about the application is specified. `module_use` can be provided to add a nonstandard path to MODULEPATH. By default BenchPRO will attempt to match this config file with its corresponsing template file. You can overwrite this default filename by adding the `template` field to this section. 
 - `[modules]` where `compiler` and `mpi` are required, while more modules can be specified if needed. Every module must be available on the local machine, if you are cross compiling to another platform (e.g. to frontera-rtx) and require system modules not present on the current node, you can set `check_modules=False` in settings.ini to bypass this check. 
 - `[config]`  where variables used in the build template script can be added.

You can define as many additional parameters as needed for your application. Eg: additional modules, build options, etc. All parameters `[param]` defined here will be used to fill `<<<[param]>>>` variables of the same name in the template file, thus consistent naming is important.
This file must be located in `$BP_HOME/config/build`, preferably with the naming scheme `[label].cfg`. 

### 2. Build template file

This template file is used to gerenate a contextualized build script which is executed to compile the application.
Variables are defined with `<<<[param]>>>` syntax and populated with the variables defined in the config file above.
If a `<<<[param]>>>` in the build template in not successfully populated and `exit_on_missing=True` in settings.ini, an expection will be raised.
You are able to make use of the `local_repo` variable defined in `$BP_HOME/settings.ini` to store and use files locally. 
This file must be located in `$BP_HOME/templates/build`, with the naming scheme `[label].template` 

### 3. Module template file (optional)

You can define your own .lua module template, otherwise a generic one will be created for you.
This file must be located in `$BP_HOME/templates/build`, with the naming scheme `[label].module` 

The application added above would be built with the following command:
```
benchpro --build [code]
```
Note: BenchPRO will attempt to match your application input to a unique config filename. The specificity of the input will depend on the number of similar config files.
It may be helpful to build with `dry_run=True` initially to confirm the build script was generated as expected, before `--removing` and rebuilding with `dry_run=False` to compile.

## Adding a new Benchmark

The process of setting up an application benchmark is much the same as the build process; a config file is used to populate a benchmark template. 

### 1. Benchmark config file

A full detailed list of config file fields is provided below. A config file is seperated into the following sections:
 - `[requirements]` where fields are defined to create requirements to an application. More fields produce a finer, more specific application selection criteria.
 - `[runtime]` where job setup parameters are defined.
 - `[config]` where bench script parameters are defined.
 - `[result]` where result collection parameters are defined.

Any additional parameters may be defined in order to setup the benchmark, i.e dataset label, problem size variables etc.
This file must be located in `$BP_HOME/config/bench`, preferably with the naming scheme `[label].cfg`.

### 2. Benchmark template file  

As with the build template. The benchmark template file is populated with the parameters defined in the config file above. This file should include setup of the dataset, any required pre-processing or domain decomposition steps if required, and the appropriate mpi_exec command.
You are able to make use of the `local_repo` variable defined in `$BP_HOME/settings.ini` to copy local files. 

This file must be located in `$BP_HOME/templates/bench`, with the naming scheme `[label].template`. 

The benchmark added above would be run with the following command:
```
benchpro --bench [dataset]
```
Note: BenchPRO will attempt to match your benchmark input to a unique config filename. The specificity of the input will depend on the number of similar config files.
It may be helpful to build with `dry_run=True` initially to confirm the build script was generated as expected, before `--removing` and rebuilding with `dry_run=False` to launch the build job.

