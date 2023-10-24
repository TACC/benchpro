====================
Handling Input Files
====================

BenchPRO provides an integrated utility for handling input files.
'Stage' is a standalone Python utility added to PATH by the BenchPRO module.

Accepts relative and absolute paths to local files, also accepts URLs.


Changing settings
-----------------


[files]
url = www.site@domain/some_files.tar

switch: sync_staging

A:
Run stage operation synchronously during BenchPRO exection.

B:
add
stage www.site@domain/some_files.tar
to job script

-save time downloading/copying files inside big jobs
-ensure input file is available and staged correctly before job starts
-

How
---

Stage first identifies the type of asset provided. It then resolves the filename and inspects the local file staging repository ($BP_REPO) for an existing copy. Stage uses the file $BP_REPO/.urllookup to store and retreive the filenames of URLs (as filenaming may not be consistant).

If a local copy is available that will be used.
Else the file will be cached to the local repo before staging for this case.


Example
-------
sync_staging=False
soft_links=True

[files] 
url = 

stage -ln ...

1st Run:

No local file
Not in urllookup
Download URL to $BP_REPO
File is archive so extract archive to $BP_REPO
Mode is ln so create symlink to working_dir
Store filename in .urllookup for future reference


2nd Run:
URL not in local repo
URL is in urlloopup
Get filename
File is archive so use extracted contents
Create symlink to working dir

Can acheive reliable behaviour using same input. Also provides flexibility to optimize workflow and reduce sched overhead.


To control this behaviour on a task-by-task basis refer to the Overload mechanic.

