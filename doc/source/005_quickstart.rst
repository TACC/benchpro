==============
Quick Start
==============

BenchPRO provides a number of example application and benchmark profiles. Lets try running an example. 

1. Load the BenchPRO module:

.. code-block::

    ml use /scratch1/hpc_tools/benchpro/modulefiles
    ml benchpro

2. Modify your SLURM allocation using the Benchsetter (bps) modifier interface:

.. code-block::
    
    bps allocation=[your allocation]

3. Build LAMMPS and run the LJ melt simualation with:

.. code-block::

    bp -B ljmelt

4. Two jobs will have started, a LAMMPS complication job, and a LJ melt benchmark job. Check the status of LAMMPS with:

.. code-block::

    bp -la
    bp -qa lammps

5. Query the state of your benchmark with:

.. code-block::

    bp -lr
    bp -qr [jobid]

6. Capture your result and provenance data to the database:

.. code-block::

    bp -C
