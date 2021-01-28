
local fn             = myFileName()                      
local full           = myModuleFullName()                
local loc            = fn:find("build",1,true)-2        
local project_dir    = fn:sub(1,loc)                    

setenv("TACC_BUILDER_DIR",                  project_dir)
prepend_path("PATH",            pathJoin(   project_dir, "python" ))
prepend_path( "MODULEPATH" ,    pathJoin(   project_dir, "build/modulefiles" ))

always_load("python3")

family("builder")
