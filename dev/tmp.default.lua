local install_path = "/scratch1/06280/mcawood/benchtool/build/frontera/cascadelake/intel19/impi19/lammps/3Mar20/default/install"

setenv("LAMMPS_DIR", install_path)
prepend_path("PATH",     pathJoin(install_path, ""))

always_load("intel/19.1.1", "impi/19.0.9")
family("LAMMPS")
