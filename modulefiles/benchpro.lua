-- BenchPRO module




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

always_load("python3")
family("benchpro")

-- Add BenchPRO module path to PYTHONPATH
local py_version =
local bps_site =
prepend_path("PYTHONPATH",         pathJoin(bps_site, "python/lib/python" .. py_version, "site-packages/" ))
prepend_path("PATH",               pathJoin(bps_site, "python/bin" ))

