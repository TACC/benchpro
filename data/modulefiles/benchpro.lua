-- BenchPRO module

local bp_site = ""
setenv("BP_SITE", bp_site)
local bp_repo = ""
setenv("BP_REPO", bp_repo)
local tacc_scratch = ""
setenv("TACC_SCRATCH", tacc_scratch )
local bp_version      = ""
setenv("BP_VERSION",  bp_version)
local build_hash      = ""
setenv("BP_BUILD_ID", build_hash) 
local py_version      = ""

-- Resolve user environment variables, $HOME, $SCRATCH, etc
local bp_home         = ""
local i,j, envName, tail = bp_home:find("$([a-zA-Z0-9]+)/(.*)")
if (i) then
  bp_home = pathJoin(os.getenv(envName), tail)
end
setenv("BP_HOME", bp_home)

local bp_apps         = ""
local i,j, envName, tail = bp_apps:find("$([a-zA-Z0-9]+)/(.*)")
if (i) then
  bp_apps = pathJoin(os.getenv(envName), tail)
end
setenv("BP_APPS",     bp_apps)

local bp_results      = ""
local i,j, envName, tail = bp_results:find("$([a-zA-Z0-9]+)/(.*)")
if (i) then
  bp_results = pathJoin(os.getenv(envName), tail)
end
setenv("BP_RESULTS",  bp_results)

-- aliases
set_alias("bp", "benchpro")
set_alias("cdb", "cd $BP_HOME")


-- add user's application directory tree to MODULEPATH
prepend_path("MODULEPATH" ,  pathJoin(bp_apps, "modulefiles" ))

-- Prompt user to clone user files if not present
if ( mode() == "load" and not isDir(bp_home) ) then
  LmodMessage(bp_home .. " not found")
  LmodMessage("Get BenchPRO user files with:")
  LmodMessage("git clone https://github.com/TACC/benchpro.git $HOME/benchpro")
  LmodMessage("")
end

always_load("python3")
family("benchpro")

-- Add BenchPRO module path to PYTHONPATH
prepend_path("PYTHONPATH",         pathJoin(bp_site, "python/lib/python" .. py_version, "site-packages/" ))
prepend_path("PATH",               pathJoin(bp_site, "python/bin" ))

