
local scratch = "/scratch"
local system = os.getenv("TACC_SYSTEM") or ""

if system == "frontera"
then
  scratch = "/scratch1"
end

setenv("TACC_SCRATCH", scratch )

local project_dir    =  
local app_dir        = 
local result_dir     =

set_alias("cbd", "cd $BT_PROJECT")

setenv("BT_PROJECT", project_dir)
setenv("BT_APPS",    app_dir)
setenv("BT_RESULTS", result_dir)

prepend_path("PATH",         pathJoin(project_dir, "src" ))
prepend_path("MODULEPATH" ,  pathJoin(app_dir, "modulefiles" ))

always_load("python3")
family("benchtool")
