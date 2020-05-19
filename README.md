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

## Adding a new application profile

### Code config file
Contains parameters which populate the template file

| Label            | Required?  | Description                                                                      |
|------------------|------------|----------------------------------------------------------------------------------|
| [general]        |            | -                                                                                |
| code             | Y          | Label for application                                                            |
| version          | Y          | Version, in the form x.x, x-x, or string like 'stable'                           |
| system           | N          | TACC system identifier, if left blank will use $TACC_SYSTEM                      |
| build_prefix     | N          | Custom build (outside of default tree)                                           |
| test_install     | N          | Read sanity check once compile is complete (WIP)                                 |
| [modules]        |            | -                                                                                |
| compiler         | Y          | Full module name of compile, eg: intel/18.0.2                                    |
| mpi              | Y          | Full module name of MPI, eg: impi/18.0.2                                         |
| [build]          |            | -                                                                                |
| arch             | N          | Provides arch specific optimization flag. If left blank with use system default  | 
| opt_flags        | N          | Can be used in conjunction with 'arch' above.                                    |
| opt_label        | N          | Custom build label, required if opt_flags is set and arch is not                 |
| bin_dir          | N          | Set bin dir suffix to add exectuable to PATH                                     | 
| [run]            |            | -                                                                                |
| exe              | Y          | Name of application executable                                                   |
| collect_hw_stats | N          | Runs the hardware state collection tool                                          |


Directory structure:
./cfgs - input config files for codes and schedulers
./build - default output directory for builds
./src - contains Python functions 
./hw_reporting - tool generate hardware state
