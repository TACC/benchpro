
local site_dir    = "/scratch1/hpc_tools/benchtool/"
setenv("BT_SITE", site_dir)

local repo_dir       = pathJoin(site_dir, "repo")
setenv("BT_REPO", repo_dir)

local scratch_root = "/scratch"
local system = os.getenv("TACC_SYSTEM") or ""

if system == "frontera"
then
  scratch_root = "/scratch1"
end

setenv("TACC_SCRATCH", scratch_root )

local home            = os.getenv("HOME")
local scratch         = os.getenv("SCRATCH")
local project_dir     = pathJoin(home, ".benchtool")
local app_dir         = pathJoin(scratch, "benchtool/build")
local result_dir      = pathJoin(scratch, "benchtool/results")
local version         = "1.1.6"

set_alias("cdb", "cd $BT_HOME")

setenv("BT_VERSION",  version)
setenv("BT_HOME",     project_dir)
setenv("BT_APPS",     app_dir)
setenv("BT_RESULTS",  result_dir)

prepend_path("PATH",         pathJoin(project_dir, "src" ))
prepend_path("MODULEPATH" ,  pathJoin(app_dir, "modulefiles" ))

always_load("python3")
family("benchtool")

local python_dir     = "/scratch1/hpc_tools/benchtool"
prepend_path("PYTHONPATH",         pathJoin(python_dir, "python/lib/python3.7/site-packages/" ))
prepend_path("PATH",               pathJoin(python_dir, "python/bin" ))

