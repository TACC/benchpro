===============================================================
BenchPRO - Benchmark Performance & Reproducibility Orchestrator
===============================================================

BenchPRO is a utility that automates, simplifies and standarizes the process of building applications, executing benchmarks and collecting results on HPC systems. 

OVERVIEW
--------

BenchPRO provides a benchmarking framework that enforces a standardized approach to compiling and running performance benchmarks. The utility automatically collects and stores significant provenance data associated with the benchmark. The framework also allows performance engineers and domain experts to share their well optimized benchmark 'recipes' in a reproducible manner. This way, someone with limited background of a workflow or science domain can run benchmarks through the framework, compare performance to previous results and examine provenance data to help identify the root cause of any discrepancies. This framework significantly enhances the reproducibility of benchmarking efforts and reduces the labor required to maintain a benchmark suite. The utility was designed to meet the following set of goals:

* Automate the process of building applications, running benchmarks and storing result data.
* Structure the framework to promote the standardization of techniques and workflows as a step towards improving benchmark reproducibility.
* Accommodate a number of benchmarking activities like comparative performance assessments, regression testing, and scalability studies.
* Store as much provenance data as possible for future reference.
* Provide an intuitive way of exploring and comparing benchmark results.


BenchPRO Basics
---------------

.. toctree::
    :maxdepth: 2

    005_quickstart       
    010_user_guide
    020_add_app
    030_add_bench
    040_testcases

Installing BenchPRO
-------------------

.. toctree::
    :maxdepth: 1

    050_db_install
    060_site_install

Advanced Topics 
---------------

.. toctree::
    :maxdepth: 1

    080_useful_features
    090_reference

BenchPRO URLs
-------------

    * Documentation    https://benchpro.readthedocs.io/en/latest/
    * Main Repo        https://github.com/TACC/benchpro
    * Database Repo    https://github.com/TACC/benchpro-db
