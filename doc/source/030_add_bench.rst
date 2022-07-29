==========================
Adding a Benchmark Profile
==========================

The process of setting up an application benchmark is much the same as the build process; a config file is used to populate a benchmark template.

Benchmark config file
---------------------

A full detailed list of config file fields is provided below. A config file is seperated into the following sections:


requirements
^^^^^^^^^^^^

where fields are defined to create requirements to an application. More fields produce a finer, more specific application selection criteria.

runtime
^^^^^^^

where job setup parameters are defined.

config
^^^^^^

where bench script parameters are defined.

result
^^^^^^

where result collection parameters are defined.

Any additional parameters may be defined in order to setup the benchmark, i.e dataset label, problem size variables etc.
This file must be located in :code:`$BP_HOME/config/bench`, preferably with the naming scheme :code:`[label].cfg`.

Benchmark template file
-----------------------

As with the build template. The benchmark template file is populated with the parameters defined in the config file above. This file should include setup of the dataset, any required pre-processing or domain decomposition steps if required, and the appropriate mpi_exec command.
You are able to make use of the :code:`local_repo` variable defined in :code:`$BP_HOME/settings.ini` to copy local files.

This file must be located in :code:`$BP_HOME/templates/bench`, with the naming scheme :code:`[label].template`.

The benchmark added above would be run with the following command:

.. code-block::
   
    benchpro --bench [dataset]

Note: BenchPRO will attempt to match your benchmark input to a unique config filename. The specificity of the input will depend on the number of similar config files.
It may be helpful to build with :code:`dry_run=True` initially to confirm the build script was generated as expected, before removing and rebuilding with :code:`dry_run=False` to launch the build job.

