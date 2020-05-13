
import subprocess
import sys

#import src.exception as exception

# Look for module, error if not available 
def check_module_exists(module, exception_logger):
    try:
        cmd = subprocess.run("ml spider "+module, shell=True, check=True, capture_output=True, universal_newlines=True)

    except subprocess.CalledProcessError as e:
        exception_logger.debug("ERROR: module "+module+" not available on this system")
        exception_logger.debug("Exitting")
        sys.exit(1)
