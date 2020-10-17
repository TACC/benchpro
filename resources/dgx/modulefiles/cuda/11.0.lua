local help_message = [[
The NVIDIA CUDA Toolkit provides a comprehensive development environment for C
and C++ developers building GPU-accelerated applications. The CUDA Toolkit
includes a compiler for NVIDIA GPUs, math libraries, and tools for debugging
and optimizing the performance of your applications. You will also find
programming guides, user manuals, API reference, and other documentation to
help you get started quickly accelerating your application with GPUs.

This module defines the environmental variables TACC_CUDA_BIN,
TACC_CUDA_LIB, TACC_CUDA_INC, TACC_CUDA_DOC, and TACC_CUDA_DIR
for the location of the cuda binaries, libaries, includes,
documentation, and main root directory respectively.

The location of the:
1.) binary files is added to PATH
2.) libraries is added to LD_LIBRARY_PATH
3.) header files is added to INCLUDE
4.) man pages is added to MANPATH


Version 11.0
]]

help(help_message,"\n")

whatis("Name: cuda")
whatis("Version: 11.0")
whatis("Category: Compiler, Runtime Support")
whatis("Description: NVIDIA CUDA Toolkit for Linux")
whatis("URL: http://www.nvidia.com/cuda")

-- Export environmental variables
local cuda_dir="/usr/local/cuda-11.0"
local cuda_bin=pathJoin(cuda_dir,"bin")
local cuda_lib=pathJoin(cuda_dir,"lib64")
local cuda_inc=pathJoin(cuda_dir,"include")
local cuda_doc=pathJoin(cuda_dir,"doc")
setenv("TACC_CUDA_DIR",cuda_dir)
setenv("TACC_CUDA_BIN",cuda_bin)
setenv("TACC_CUDA_LIB",cuda_lib)
setenv("TACC_CUDA_INC",cuda_inc)
setenv("TACC_CUDA_DOC",cuda_doc)
prepend_path("PATH"           ,cuda_bin)
prepend_path("LD_LIBRARY_PATH",cuda_lib)
prepend_path("INCLUDE"        ,cuda_inc)
prepend_path("MANPATH"        ,pathJoin(cuda_doc,"man"))
add_property("arch","gpu")

