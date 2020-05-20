# bench-framework
Framework to automate benchmarking of largescale HPC systems

## Gettiing Started

```
git clone
cd bench-framework
source load_env.sh
```
Show list of applications available to install
```
benchtool --avail
```
Install a new application
```
benchtool --install lammps
```
Show list of applications currently installed
```
benchtool --installed
```
Remove intalled application
```
benchtool --remove stampede2/intel18/impi18/lammps/skylake/stable
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

### 1. Code config file
Contains parameters which populate the template file

| Label            | Required?  | Description                                                                      |
|------------------|------------|----------------------------------------------------------------------------------|
| **[general]**        |            | -                                                                            |
| code             | Y          | Label for application                                                            |
| version          | Y          | Version, in the form x.x, x-x, or string like 'stable'                           |
| system           | N          | TACC system identifier, if left blank will use $TACC_SYSTEM                      |
| build_prefix     | N          | Custom build (outside of default tree)                                           |
| test_install     | N          | Read sanity check once compile is complete (WIP)                                 |
| **[modules]**        |            | -                                                                            |
| compiler         | Y          | Full module name of compile, eg: intel/18.0.2                                    |
| mpi              | Y          | Full module name of MPI, eg: impi/18.0.2                                         |
| **[build]**         |            | -                                                                             |
| arch             | N          | Provides arch specific optimization flag. If left blank with use system default  | 
| opt_flags        | N          | Can be used in conjunction with 'arch' above.                                    |
| opt_label        | N          | Custom build label, required if opt_flags is set and arch is not                 |
| bin_dir          | N          | Set bin dir suffix to add exectuable to PATH                                     | 
| **[run]**            |            | -                                                                            |
| exe              | Y          | Name of application executable                                                   |
| collect_hw_stats | N          | Runs the hardware state collection tool                                          |

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
