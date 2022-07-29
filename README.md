![Lmod Logo](https://github.com/TACC/benchpro-site/raw/main/benchpro/resources/images/benchpro_grey.png)

[![Documentation Status](https://readthedocs.org/projects/benchpro/badge/?version=latest)](https://benchpro.readthedocs.io/en/latest/?badge=latest)


# BenchPRO-site
BenchPRO - Benchmark Performance & Reproducibility Orchestrator, is a framework to automate and standardize application compilation, benchmarking and result collection on large scale HPC systems. This repo provides the site package, refer to the 

## BenchPRO URLs

- Documentation    https://benchpro.readthedocs.io/en/latest/
- Client Repo      https://github.com/TACC/benchpro
- Site Repo        https://github.com/TACC/benchpro-site
- Database Repo    https://github.com/TACC/benchpro-db


## Site Installation

Before installing ensure that your system has a stanza in the `site.sh` contextualization file. BenchPRO is installed as a Python3 package.

1 Load system Python3 module
``` 
ml python3
```

2 Download and install BenchPRO package: 
```
git clone https://github.com/TACC/benchpro-site.git
cd benchpro-site
./install.sh [key]
```

You can optionally provide an SSH private key for authentication to the database server, if no key is provided the default user key will be used. The installation script will perform a number of checks during installation to assist in troubleshooting if errors arise. By default, the installation script will limit access to the package directory to current unix group (G-25072 on TACC systems).

If the installation and validation steps complete successfully, a set of two cronjobs will be displayed, the first to automatically sync provenance files to the database server every 5 minutes, and the second to sync the master local file repository, $BP_REPO - typically in /work, to the scratch file system, providing a shared repo between systems.  

## User Repo

In order to use BenchPRO, users need to install a local instance of the configuration and template files into their home directory. For additional information on how to install the user files and BenchPRO usage information, refer to the user repository here: https://github.com/TACC/benchpro

The user files repository was installed as part of the process described above for setup validation.

### Version Control

The user repository version number in $BP_HOME/.version is tested against the package version number $BPS_SITE_VERSION to ensure compatibility between the two repositories. If users are running an old version, they will be prompted to update when using the utility. If changes are made to this repository, the version should be updated with the provided script:
```
./dev/version.sh [x.y.z]
```
You will then have to push changes to the user file repository (follow instructions provided) before rerunning the `install.sh` script so that versioning is consistent.

## Web server

Captured applications and benchmark results are available via a web frontend at http://tacc-stats03.tacc.utexas.edu/. 

In order to submit application and benchmark data to the database server from a new host, its IP address needs to be added to the database whitelist file `/home/postgres/9.6/data/pg_hba.conf`. Ensure you restart the database to read the updated file:
```
systemctl restart postgresql
```
