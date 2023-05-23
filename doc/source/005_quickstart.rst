==============
Quick Start
==============

.. _quickstart:

BenchPRO provides a number of example application and benchmark profiles. This Quick Start walks through the process of building an application, running a benchmark and capturing the result on Frontera.

1. Load the BenchPRO module:

.. code-block::

    ml use /scratch1/hpc_tools/benchpro/modulefiles
    ml benchpro

2. Provide your SLURM allocation using the BPS settings interface:

.. code-block::
    
    bps allocation=[your allocation]

3. Build LAMMPS and run the LJ melt simualation with:

.. code-block::

    bp -b lammps
    bp -B ljmelt

4. Two jobs will have started, a LAMMPS complication job, and a LJ melt benchmark job. Check the status of LAMMPS with:

.. code-block::

    bp -la
    bp -qa lammps

5. Query the state of your benchmark with:

.. code-block::

    bp -lr
    bp -qr [jobid]

6. Once the jobs are complete, capture your result and provenance data to the database:

.. code-block::

    bp -C
