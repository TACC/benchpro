![BenchPRO Logo](https://github.com/TACC/benchpro/raw/main/benchpro/resources/images/benchpro_grey.png)
[![Documentation Status](https://readthedocs.org/projects/benchpro/badge/?version=latest)](https://benchpro.readthedocs.io/en/latest/?badge=latest)


# BenchPRO
BenchPRO - Benchmark Performance & Reproducibility Orchestrator, is a framework to automate and standardize the process of application compilation, benchmarking and result collection on large scale HPC systems. 

## BenchPRO URLs

- Documentation    https://benchpro.readthedocs.io/en/latest/
- Main Repo        https://github.com/TACC/benchpro
- Database Repo    https://github.com/TACC/benchpro-db


## Getting Started

### Install

The BenchPRO site package should already be installed on most TACC systems. If it is not, contact mcawood@tacc.utexas.edu or install it from the [benchpro](https://github.com/TACC/benchpro) repository. Assuming the site package is available, you need to install a local copy of the configuration and template files to use BenchPRO.

| System             | Module Path                              |
|--------------------|------------------------------------------|
| Frontera           | /scratch1/hpc\_tools/benchpro/modulefiles|
| Stampede2          | /scratch/hpc\_tools/benchpro/modulefiles |
| Lonestar6          | /scratch/projects/benchpro/modulefiles  |

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
5 Display some useful info
```
benchpro --notices
benchpro --defaults
```
These defaults are set by the $BP\_HOME/user.ini 


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
You will see that this installation of LAMMPS was a dry run. This means that BenchPRO generated a LAMMPS compilation script but did not submit it to the scheduler to execute the build process. You can obtain more information about your dry install of LAMMPS with:
```
benchpro -qa lammps
```
You can examine the build script `job.qsub` located in the `path` directory. Submit your LAMMPS compilation script to the scheduler manually, or
4 Remove this instance of LAMMPS with:
```
benchpro -da lammps
```
5 Overload the default 'dry\_run' value and rebuild LAMMPS with: 
```
benchpro -b lammps -o dry\_run=False
```
Overloading settings on the command line will only take effect once, to permentantly disable dry\_run mode, use the interface tool 'bps':
```
bps dry_run=False
```
6 Now check the status of your LAMMPS compilation job with:
```
benchpro -qa lammps
```
In this example, parameters in `$BPS_INC/build/config/lammps.cfg` were used to contextualize the build template `$BPS_INC/build/templates/lammps.template` and produce a job script. Parameters for the job, system architecture, compile time optimizations and a module file were automatically generated. You can load your LAMMPS module with `ml lammps`. For each application that is built, a 'build\_report' is generated in order to preserve metadata about the application. This build report is referenced whenever the application is used to run a benchmark, and also when this application is captured to the database. You can manually examine this report in the application directory or by using the `--queryApp / -qa` flag.

### Run a Benchmark

We can now run a benchmark with our LAMMPS installation. There is no need to wait for the LAMMPS build job to complete because BenchPRO is able create job dependencies between tasks when needed. In fact, if `build_if_missing=True` in `$BP_HOME/user.ini`, BenchPRO would detect that LAMMPS is not installed for the current system when attempting to run a benchmark and build it automatically without us doing the steps above. The process to run a benchmark is similar to compilation; a configation file is used to populate a template script. A benchmark run is specified with `--bench / -B`. The argument may be a single benchmark label, or a benchmark 'suite' (i.e collection of benchmarks) defined in `user.ini`. Once again you can check for available benchmarks with `--avail / -a`.  

1 If you haven't already, disable the dry\_run mode.
```
bps dry_run=False
```
2 Execute a LAMMPS Lennard-Jones benchmark run with: 
```
benchpro -B ljmelt 
```
We changed `user.ini` so we don't need to use the `--overload / -o` flag to disable the dry\_run mode. 
Note that BenchPRO will use the appropriate scheduler defaults for the current system. You can overload individual parameters using `--overload`, or use another scheduler config file with the flag `--sched [FILENAME]`. 

3 Check the benchmark report with:
```
benchpro -qr ljmelt
```
4 Because this Lennard-Jones benchmark was the last BenchPRO job executed, a useful shortcut is available to check this report:
```
benchpro --last
```

In this example, parameters in `$BPS_INC/bench/config/lammps_ljmelt.cfg` were used to contextualize the template `$BPS_INC/bench/templates/lammps.template`
Much like the build process, a 'bench\_report' was generated to store metadata associated with this benchmark run. It is stored in the benchmark result direcotry and will be used in the next step to capture the result to the database.

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

## Site Installation

Before installing, ensure that your system has a stanza in the `site.sh` contextualization file. BenchPRO is installed as a Python3 package.

1 Load system Python3 module
``` 
ml python3
```

2 Download and install BenchPRO package: 
```
git clone https://github.com/TACC/benchpro.git
cd benchpro
./INSTALL [key]
```

You can optionally provide an SSH private key for authentication to the database server, if no key is provided the default user key will be used. The installation script will perform a number of checks during installation to assist in troubleshooting if errors arise. By default, the installation script will limit access to the package directory to current unix group (G-25072 on TACC systems).

If the installation and validation steps complete successfully, a set of two cronjobs will be displayed, the first to automatically sync provenance files to the database server every 5 minutes, and the second to sync the master local file repository, $BP\_REPO - typically in /work, to the scratch file system, providing a shared repo between systems.  

## Web server

Captured applications and benchmark results are available via a web frontend at http://tacc-stats03.tacc.utexas.edu/. 

In order to submit application and benchmark data to the database server from a new host, its IP address needs to be added to the database whitelist file `/home/postgres/9.6/data/pg_hba.conf`. Ensure you restart the database to read the updated file:
```
systemctl restart postgresql
```
