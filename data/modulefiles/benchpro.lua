-- BenchPRO module

local bt_site = ""
setenv("BP_SITE", bt_site)
local bt_repo = ""
setenv("BP_REPO", bt_repo)
local tacc_scratch = ""
setenv("TACC_SCRATCH", tacc_scratch )
local bt_version      = ""
setenv("BP_VERSION",  bt_version)
local py_version      = ""

-- Resolve user environment variables, $HOME, $SCRATCH, etc
local bt_home         = ""
local i,j, envName, tail = bt_home:find("$([a-zA-Z0-9]+)/(.*)")
if (i) then
  bt_home = pathJoin(os.getenv(envName), tail)
end
setenv("BP_HOME", bt_home)

local bt_apps         = ""
local i,j, envName, tail = bt_apps:find("$([a-zA-Z0-9]+)/(.*)")
if (i) then
  bt_apps = pathJoin(os.getenv(envName), tail)
end
setenv("BP_APPS",     bt_apps)

local bt_results      = ""
local i,j, envName, tail = bt_results:find("$([a-zA-Z0-9]+)/(.*)")
if (i) then
  bt_results = pathJoin(os.getenv(envName), tail)
end
setenv("BP_RESULTS",  bt_results)

-- cdb alias
set_alias("cdb", "cd $BP_HOME")

-- add user's application directory tree to MODULEPATH
prepend_path("MODULEPATH" ,  pathJoin(bt_apps, "modulefiles" ))

-- Prompt user to clone user files if not present
if ( mode() == "load" and not isDir(bt_home) ) then
  LmodMessage(bt_home .. " not found")
  LmodMessage("Get BenchPRO user files with:")
  LmodMessage("git clone https://github.com/TACC/benchpro.git $HOME/benchpro")
  LmodMessage("")
end

always_load("python3")
family("benchpro")

-- Add BenchPRO module path to PYTHONPATH
prepend_path("PYTHONPATH",         pathJoin(bt_site, "python/lib/python" .. py_version, "site-packages/" ))
prepend_path("PATH",               pathJoin(bt_site, "python/bin" ))

