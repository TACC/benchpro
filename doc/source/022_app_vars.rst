=====================
Template variables
=====================


BenchPRO creates a development ecosystem for the user. When writing BenchPRO template you should keep in mind:

1. BenchPRO creates a working directory for this task 'working_dir'. The script will be run from there so "." = working_dir
2. Everything associated with a task is contained within the job script. There is no external magic. Jobs can be launched outside of benchpro
3. BenchPRO (bp, benchro, bps, stage) will be in PATH. Modules under [modules] will be loaded. Modulefile of dependent applications will be loaded.

important vars
working_dir
install_dir



