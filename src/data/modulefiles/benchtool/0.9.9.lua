
local scratch = "/scratch"
local system = os.getenv("TACC_SYSTEM") or ""

if system == "frontera"
then
  scratch = "/scratch1"
end

setenv("TACC_SCRATCH", scratch )

local install_dir    =  
local build_dir      = 

setenv("BENCHTOOL", install_dir)
prepend_path("PATH",         pathJoin(install_dir, "src" ))
prepend_path("MODULEPATH" ,  pathJoin(build_dir, "modulefiles" ))

always_load("python3")
family("benchtool")
