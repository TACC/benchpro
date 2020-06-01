# bench-framework
This is a framework to automate and standardize application benchmarking on largescale HPC systems.

Currently there are 5 application profiles available for testing:
   - OpenFoam
   - LAMMPS
   - WRF
   - Quantum Espresso
   - SWIFTsim

## Getting Started

The following steps should produce a working installation of LAMMPS. Tested on Stampede2 and Frontera.


1 Download and setup env: 

```
git clone https://gitlab.tacc.utexas.edu/mcawood/bench-framework
cd bench-framework
source load_env.sh
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
benchtool --install lammps
```
5 List applications currently installed:
```
benchtool --installed
```
By default `dry_run=True` in `settings.cfg` so the build script was created but not submitted to the scheduler. You could submit the job manually, or


6 remove the dry_run build:
```
benchtool --remove [output from above]
```
7 change `dry_run=False` in `settings.cfg` and rerun: 
```
benchtool --install lammps
```
You should see the job has been submitted. After the job is complete, update your MODULEPATH:
```
source load_env.sh
``` 
and confirm the LAMMPS module is available:
```
ml avail
```
load the LAMMPS module and confirm that the LAMMPS binary is in your PATH:
```
ml [lammps_module]
which lmp_intel_cpu_intelmpi
```
In this example, parameters in `config/build/lammps_build.cfg` were used to populate the template `templates/build/lammps-stable.build`

## Running a benchmark

Assuming the above process was successful, you can now run a benchmark using your installed application.
The benchmark process is similar to building; a config file is used to populate a template.
A benchmark .cfg file can be provided with the `--param`, if no input is provided, the default cfg file will be used, located in `config/run/`  


Run the LAMMPS benchmark with: 
```
benchtool --run lammps
```


## Global settings

Global settings are defined in the file `settings.cfg`

| Label            | Default  | Description                                                                      |
|------------------|------------|----------------------------------------------------------------------------------|
| **[builder]**    |            | -                                                                            |
| dry_run           | True       | Generates job script but does not submit it, useful for testing
| use_default_paths | True       | Overwrites setting in application config file (below), builds app in default location |
| overwrite         | False      | If existing installation  is found in build path, replace it                |
| exit_on_missing   | True       | Exit if template is not fully populates (missing parameters found)            |
| log_level         | 1          | WIP                                                                      |                
| exception_log_file| error      | Label for exception log                                                         |                                 
| build_log_file    | build      | Label for build log                                                              |
| **[bencher]**    |            |                                                                                  |
| run_log_file      | run        | Label for run log                                                              |

## Adding a new application profile
The builder requires two input files to build an application: a config file containing contextualization parameters, and a build template file which will be populated with this parameters. 

### 1. Contextualization Config file
This file contains parameters which populate the template file, the file is broken in sections corresponding to general settings, system modules required, build and run parameters.

| Label            | Required?  | Description                                                                      |
|------------------|------------|----------------------------------------------------------------------------------|
| **[general]**        |            |                                                                           |
| code             | Y          | Label for application                                                            |
| version          | Y          | Version, in the form x.x, x-x, or string like 'stable'                           |
| system           | N          | TACC system identifier, if left blank will use $TACC_SYSTEM                      |
| build_prefix     | N          | Custom build (outside of default tree)                                           |
| test_install     | N          | Read sanity check once compile is complete (WIP)                                 |
| **[modules]**        |            |                                                                         |
| compiler         | Y          | Module name of compile, eg: 'intel/18.0.2' or just 'intel' for system default.   |
| mpi              | Y          | Module name of MPI, eg: 'impi/18.0.2' or just 'impi' for system default.          |
| **[build]**         |            |                                                                           |
| arch             | N          | Generates archicture specific optimization flags. If left blank will use system default, set to 'system' to combine with 'opt_flags' below  | 
| opt_flags        | N          | Used to add additional optimization flags, eg: '-g -ipo'  etc.  If arch is not set, this will be only optimzation flags used.        |
| opt_label        | N          | Custom build label, replaces arch default eg: skylake-xeon. Required if 'opt_flags' is set and 'arch' is not                 |
| bin_dir          | N          | Set bin dir suffix to add exectuable to PATH, eg: bin, run etc.                                     | 
| **[run]**            |            |                                                                          |
| exe              | Y          | Name of application executable                                                   |
| collect_hw_stats | N          | Runs the hardware state collection tool before benchmark                                         |

You can define as many additional labels as needed for your application. Eg: additional modules, build options etc.
This file must be located in `configs/codes`, with the naming scheme `[code]_build.cfg`

### 2. Code template file

This file is the template for the scheduler job script which will compile the application.
Variables are defined with `<<<[label]>>>` and populated with the variables defined in the config file above.
The label in the template must match the label used in the config file.  

This file must be located in `templates/codes`, with the naming scheme `[code]-[version].build` 

### 3. Module template file (optional)

You can define you own Lua module template, otherwise a generic one will be created for you.
This file must be located in `templates/codes`, with the naming scheme `[code]-[version].module` 

## Directory structure

./config - input config files for codes and schedulers 


./build - default output directory for builds


./src - contains Python functions 


./hw_reporting - tool generate hardware state


./templates - input template files 
