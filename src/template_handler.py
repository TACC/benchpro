# System Imports
import re
import shutil as su
import sys

import src.exception as exception
import src.global_settings as gs

logger = ''

# Copy template files for population


def construct_template(input_templates, script_file):
    with open(script_file, 'wb') as out:
        for f in input_templates:
            # Get full path the input template file
            f = gs.base_dir + gs.sl + gs.template_dir + gs.sl + f
            logger.debug("Ingesting template file " + f)

            with open(f, 'rb') as fd:
                su.copyfileobj(fd, out)

# Contextualize build template with input.cfg vars


def populate_template(input_cfgs, script_file):

    script = open(script_file).read()
    # Look for matching cfg labels in template and replace
    for cfg in input_cfgs:
        for key in cfg:
            logger.debug("replace " + "<<<" + str(key) +
                         ">>> with " + str(cfg[key]))
            script = script.replace("<<<" + str(key) + ">>>", str(cfg[key]))
    return script

# Check for unpopulated vars in template file


def test_template(script):
    key = "<<<.*>>>"
    nomatch = re.findall(key, script)
    if len(nomatch) > 0:
        logger.debug("Missing build parameters were found in build template!")
        logger.debug(nomatch)
        if gs.exit_on_missing:
            exception.error_and_quit(
                logger, "Missing parameters were found after populating the template and exit_on_missing=True in settings.cfg:" + ' '.join(nomatch))
    else:
        logger.debug("All build parameters were filled, continuing")

# Write template to file


def generate_template(input_cfgs, input_templates, script_file, log_to_use):
    global logger
    logger = log_to_use

    # Take multiple input template files and combine them to generate unpopulated script
    construct_template(input_templates, script_file)

    # Take multiple config dicts and populate script template
    script = populate_template(input_cfgs, script_file)

    # Test for missing parameters
    test_template(script)

    # Read populated script to file
    with open(script_file, "w") as f:
        f.write(script)
