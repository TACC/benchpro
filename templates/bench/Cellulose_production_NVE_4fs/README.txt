This is Cellulose in a TIP3P Water box - 408,609 atoms.

Run on multiple CPUs with e.g.:

mpirun -np 4 $AMBERHOME/exe/pmemd -O -i mdin -o mdout -p prmtop -c inpcrd

Run on a GPU with e.g.:

$AMBERHOME/exe/pmemd.cuda -O -i mdin -o mdout -p prmtop -c inpcrd

This is a more realistic version of the Cellulose benchmark run with what would
be typical NVE production parameters.  It uses shake with a 4fs timestep.  It
has a 9 Angstrom cutoff and writes output and trajectory files every 1000 steps
(4ps). Additionally, it writes the restart file only at the end of this short
run.  For performance reasons, it is set to produce NETCDF binary trajectory
files.
