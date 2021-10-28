-- BenchTool module

local bt_site = ""
setenv("BT_SITE", bt_site)
local bt_repo = ""
setenv("BT_REPO", bt_repo)
local tacc_scratch = ""
setenv("TACC_SCRATCH", tacc_scratch )
local bt_version      = ""
setenv("BT_VERSION",  bt_version)
local py_version      = ""

-- Resolve user environment variables, $HOME, $SCRATCH, etc
local bt_home         = ""
local i,j, envName, tail = bt_home:find("$([a-zA-Z0-9]+)/(.*)")
if (i) then
  bt_home = pathJoin(os.getenv(envName), tail)
end
setenv("BT_HOME", bt_home)

local bt_apps         = ""
local i,j, envName, tail = bt_apps:find("$([a-zA-Z0-9]+)/(.*)")
if (i) then
  bt_apps = pathJoin(os.getenv(envName), tail)
end
setenv("BT_APPS",     bt_apps)

local bt_results      = ""
local i,j, envName, tail = bt_results:find("$([a-zA-Z0-9]+)/(.*)")
if (i) then
  bt_results = pathJoin(os.getenv(envName), tail)
end
setenv("BT_RESULTS",  bt_results)

-- cdb alias
set_alias("cdb", "cd $BT_HOME")

-- add user's application directory tree to MODULEPATH
prepend_path("MODULEPATH" ,  pathJoin(bt_apps, "modulefiles" ))

-- Prompt user to clone user files if not present
if ( mode() == "load" and not isDir(bt_home) ) then
  LmodMessage(bt_home .. " not found")
  LmodMessage("Get BenchTool user files with:")
  LmodMessage("git clone https://github.com/TACC/benchtool.git $HOME/benchtool")
  LmodMessage("")
end

always_load("python3")
family("benchtool")

-- Add BenchTool module path to PYTHONPATH
prepend_path("PYTHONPATH",         pathJoin(bt_site, "python/lib/python" .. py_version, "site-packages/" ))
prepend_path("PATH",               pathJoin(bt_site, "python/bin" ))

