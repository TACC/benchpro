-- BenchPRO module

local help_msg=[[

BenchPRO is a benchmarking framework that enforces a standardized approach to compiling and 
running benchmarks. Additionally, the framework automatically records significant provenance and 
performance data for reference. The framework allows domain experts to share their well optimized 
applications and representative benchmark datasets in a reproducible manner. This way, an 
individual with a limited scientific or application background can run benchmarks through the 
framework, compare performance to previous results and examine provenance data to help identify 
the root cause of any discrepancies. This framework significantly enhances the reproducibility of 
benchmarking efforts and reduces the labor required to maintain a benchmark suite.

Documentation    - https://benchpro.readthedocs.io/en/latest/
Client Repo      - https://github.com/TACC/benchpro
Site Repo        - https://github.com/TACC/benchpro-site
Database Repo    - https://github.com/TACC/benchpro-db

# First time setup:
-------------------

1. Load this module:
> ml use /scratch1/hpc_tools/benchpro/modulefiles
> ml benchpro

2. Run initialization & validation:
> benchpro --validate

3. Print help:
> benchpro --help
> benchpro --defaults
> benchpro --notices

4. Build application and run benchmark:
> benchpro -a
> benchpro -b [app]
> benchpro -B [dataset]

5. Capture result 
> benchpro -C

# User Variables:
-----------------
BP_HOME         - Directory for user application and benchmark config & template files
BP_APPS         - Directory for applications built with BenchPRO
BP_RESULTS      - Directory for benchmarks run with BenchPRO
BP_REPO         - Directory for BenchPRO's per-user file caching feature
BP_NOTICE       - [1]: print site notices, [0], ignore notices
BP_DEV          - [1]: use development release, [0]: use production (default)
BP_DEBUG        - same as "debug=" in $BP_HOME/user.ini, turns on/off additional output

# Maintainer Variables:
-----------------------
BPS_HOME        - Base directory for BenchPRO site package
BPS_BIN         - Python3 executables
BPS_INC         - Reference configs/templates
BPS_COLLECT     - Result collection caching directory
BPS_MODULES     - Site module directory
BPS_SYSTEM      - Site on which BenchPRO is installed [frontera/stampede2/lonestar6]
BPS_VERSION     - BenchPRO version number
BPS_VERSION_STR - Full version string, format: [release.version.number]-[buildhash].[validator sync]
BPS_LOG         - Site installation log file

Version:
]]

help(help_msg)

-- Resolve user environment variables, $HOME, $SCRATCH, etc
local bp_home         = 
local i,j, envName, tail = bp_home:find("$([a-zA-Z0-9]+)/(.*)")
if (i) then
  bp_home = pathJoin(os.getenv(envName), tail)
end
setenv("BP_HOME", bp_home)

local bp_repo         =
local i,j, envName, tail = bp_repo:find("$([a-zA-Z0-9]+)/(.*)")
if (i) then
  bp_repo = pathJoin(os.getenv(envName), tail)
end
setenv("BP_REPO", bp_repo)

local bp_apps         = 
local i,j, envName, tail = bp_apps:find("$([a-zA-Z0-9]+)/(.*)")
if (i) then
  bp_apps = pathJoin(os.getenv(envName), tail)
end
setenv("BP_APPS",     bp_apps)

local bp_results      = 
local i,j, envName, tail = bp_results:find("$([a-zA-Z0-9]+)/(.*)")
if (i) then
  bp_results = pathJoin(os.getenv(envName), tail)
end
setenv("BP_RESULTS",  bp_results)

-- aliases
set_alias("bp", "benchpro")
set_alias("bps", "benchset")
set_alias("cdb", "cd $BP_HOME")
set_alias("bp_switch", "source $BPS_BIN/toggle_dev_prod")

-- add user's application directory tree to MODULEPATH
prepend_path("MODULEPATH" ,  pathJoin(bp_apps, "modulefiles" ))

depends_on("python3")
family("benchpro")

-- Add BenchPRO module path to PYTHONPATH
local py_version =
local bps_site =
prepend_path("PYTHONPATH",         pathJoin(bps_site, "python/lib/python" .. py_version, "site-packages/" ))
prepend_path("PATH",               pathJoin(bps_site, "python/bin" ))
