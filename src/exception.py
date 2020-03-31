# System Imports
import sys

# Local Imports
import src.utils as utils

def var_not_filled(logger):
    logger.debug("Exception thrown, var not filled, exiting!")
    sys.exit(1)

def input_missing(input, logger):
    logger.debug("Input file \"" + str(input) + "\" not found, exiting!")
    sys.exit(1)
