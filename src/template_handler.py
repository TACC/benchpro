# System Imports
import re
import shutil as su
import sys

import src.exception as exception

# Copy template files for population
def construct_template(list_of_templates, job_script):
    with open(job_script,'wb') as out:
        for f in list_of_templates:
            with open(f,'rb') as fd:
                su.copyfileobj(fd, out)

# Contextualize build template with input.cfg vars
def populate_template(template_opts, script, build_logger):
    for key in template_opts:
        build_logger.debug("replace " + "<<<" + str(key) + ">>> with " + str(template_opts[key]))
        script = script.replace("<<<" + str(key) + ">>>", str(template_opts[key]))
    return script

# Check for unpopulated vars in template file
def test_template(script, exit_on_missing, build_logger, exception_logger):
    key = "<<<.*>>>"
    nomatch = re.findall(key,script)
    if len(nomatch) > 0:
        build_logger.debug("Missing build parameters were found in build template!")
        build_logger.debug(nomatch)
        if exit_on_missing:
            exception.error_and_quit(exception_logger, "Missing parameters were found in build template and exit_on_missing=True in settings.cfg:"+' '.join(nomatch))
    else:
        build_logger.debug("All build parameters were filled, continuing")

# Write template to file
def write_template(script_file, script):
    with open(script_file, "w") as f:
        f.write(script)

