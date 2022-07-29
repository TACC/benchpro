
import glob
import os
import subprocess
import sys

# If an urgent message is in $BPS_SITE/notices/urgent, print them and quit

def run_files(notice_path):
    if os.path.isdir(notice_path):
        for notice_file in glob.glob(notice_path+"/*.txt"):
            with open(notice_file, 'r') as f:
                print(f.read())
            
            
# Print urgent (terminating) and non-urgent messages
def print_notices():

    # Skip
    if not (str(os.environ.get("BP_NOTICE")) == "1"):
        print("(export BP_NOTICE=1 for help)")
        return

    # !!!THIS CAN BE EDITTED: DISABLE NOTICES!!! 
    print_notices = True
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    if print_notices:

        # Condition
        out_of_date_user = False
        # Quit if old dir exists
        dir_exists = os.path.expandvars("$HOME/benchpro/config")
        if os.path.isdir(dir_exists):
            out_of_date_user = True

        # PROD
        hard_coded_path = "/scratch1/hpc_tools/benchpro/package/benchpro/notices"
        if os.environ.get("BP_DEV") == "1":
            # DEV
            hard_coded_path = "/scratch1/08780/benchpro/benchpro-dev/package/benchpro/notices"
        run_files(hard_coded_path)


        print()
        print()
        print()
        print("You are running an old (incompatible) version of BenchPRO!")
        print()

        if out_of_date_user:
            print("You appear to be an existing user? (at least you have a $HOME/benchpro/config, so that's cool.)")
            print("Please complete this one-time migrate step to the newest and (far better) BenchPRO 1.6.0.")
            print("We're going to need you to backup your old application and benchmkark files so that they will survive the purge step later...")
            print(">   mv ~/benchpro ~/benchpro.old")
            print()

        else:
            
            print("You look new round here?")
            print("Please complete this one-time initialization step to the newest and (far better) BenchPRO 1.6.0.")
            print("You should head over to the docs and run through setting up BenchPRO in \"User Setup\":")
            print("     https://benchpro.readthedocs.io/en/latest/070_user_setup.html")
            print()
            print("Then building LAMMPS and running the LJ-Melt benchmark in \"New User Guide\":")
            print("     https://benchpro.readthedocs.io/en/latest/010_user_guide.html")
            print()


        print("1. You will have to remove any existing applications and benchmarks installed with BenchPRO (unfortunately), do this with:")
        print(">   bp --purge")
        print()

        print("2.A. If you are a non TACC staff member without SSH keys to https://github.com/TACC/benchpro")
        print("    Grab the new restructured user file repo via HTTPS")
        print(">   git clone https://github.com/TACC/benchpro.git ~/benchpro")
        print()
        print("!__OR__! ")
        print()        
        print("2.B. If you are a TACC staff member with SSH key access to https://github.com/TACC/benchpro")
        print("    Grab the new restructured user file repo via SSH key:")
        print(">   git clone https://github.com/TACC/csa.git $BP_HOME/")
        print(">   git switch [csa_branch_label]")
        print("Add your application (https://benchpro.readthedocs.io/en/latest/020_add_app.html)")
        print("and benchmark (https://benchpro.readthedocs.io/en/latest/030_add_bench.html) .cfg profiles, then push to your branch.")
        print("Refer to recommended branch naming convention below.")
        print

        print("3.You can conintue as an un-affiliated BenchPRO user - doing work unrelated to LCCF CSA.")
        print("    If you are a CSA group member, contact your TACC support laison to create your CSA branch.")
        print("    or try:")
        print(">   cd $BP_HOME")
        print(">   git fetch")
        print(">   git switch [csa-pi]")
        print(">   git pull")
        print("Refer to recommended branch naming convention below.")
        print()

        print("4. Generate your directory structure by running the validator:")
        print(">   bp --validate")
        print("5. You now have a new $BP_HOME file structure created for you.")
        print("The file $BP_HOME/settings.ini contains key-value pairs, under your control, that can 'overwrite' the system level defined defaults.")
        print("TLDR: these permenent 'overwrite' key-values can be apploied to ANY parameter within BenchPRO, e.g:")
        print("    parameters like: 'queue', 'benchmark_label', $git_tag, 'runtime', 'nodes', 'mpi_ranks_per_node', 'OMP_NUM_THREADS', etc.")
        print("key-value pairs in $BP_HOME/settings.ini will be enforced/overwritten where ever needed, and an error will be raise if a overwriting key-value pair goes unused.")
        print("Run 'bp --defaults' for more info.")
        print()

        print("6. If you are an existing user and backed up your CSA's application and benchmark .cfg and .template files to ~/benchpro.old, now's the time to restore them.")
        print("(NOTE: the directroy structure for these files has changed by popular request):")
        print(">   cp ~/benchpro.old/config/build/[app.cfg] ~/benchpro/build/config/")
        print(">   cp ~/benchpro.old/template/bench/[app.cfg] ~/benchpro/bench/config/")
        print()

        print("7. Confirm your application was copied correctly and is visible to BenchPRO with:")
        print(">   bp -a")
        print("(under the \"$BP_HOME/build/config:\" section)")
        print()

        print("8. Now you can rebuild your application, or get more walkthrough info at:")
        print("   https://benchpro.readthedocs.io/en/latest")
        print()

        print("You can build the reference LAMMPS application with:")
        print(">  bp -b lammps -o queue=debug")
        print("(the debug queue is for TACC staff only, users leave that off)")
        print() 


        print("In order to share files between members of you CSA group, I suggest you checkout your own branch.")
        print("Only TACC staff that have SSH keys setup to access https://github.com/TACC/benchpro can push.")

        print("Here is a proposed naming convention for each CSA group:")
        print("--------------")
        print("  csa-amaro")
        print("  csa-bodony")
        print("  csa-chelikowsky")
        print("  csa-choi")
        print("  csa-chong")
        print("  csa-cui")
        print("  csa-gabriel")
        print("  csa-gettelman")
        print("  csa-giustino")
        print("  csa-gottlieb")
        print("  csa-gurnis")
        print("  csa-norman")
        print("  csa-orf")
        print("  csa-quinn")
        print("  csa-rahnemoonfar")
        print("  csa-riedel")
        print("  csa-stone")
        print("  csa-tajkhorshid")
        print("  csa-wang")
        print("  csa-yeung")
        print("--------------")
        print()

        print("I suggest each TACC liason branch from ")
        print("Please DO NOT! push to main. I will be upset.")





        sys.exit(1)
