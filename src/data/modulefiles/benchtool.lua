
local install_dir    = "$HOME/.benchtoool"                  
local build_dir      = "$SCRATCH/benchtool/build"

prepend_path("PATH",            pathJoin(   project_dir, "python" ))
prepend_path( "MODULEPATH" ,    pathJoin(   build_dir, "modulefiles" ))

always_load("python3")

family("benchtool")
