# System Imports
import re
import shutil as su
import sys

# Copy template files for population
def construct_template(sched_template, compiler_template, build_template, job_script):
    with open(job_script,'wb') as out:
        for f in [sched_template, compiler_template, build_template]:
            with open(f,'rb') as fd:
                su.copyfileobj(fd, out)

# Contextualize build template with input.cfg vars
def populate_template(template_opts, script, build_logger):
    for key in template_opts:
        print(key)
        build_logger.debug("replace " + "<<<" + key + ">>> with " + template_opts[key])
        script = script.replace("<<<" + key + ">>>", template_opts[key])
    return script

# Check for unpopulated vars in template file
def test_template(script, exit_on_missing, build_logger, exception_logger):
    key = "<<<.*>>>"
    nomatch = re.findall(key,script)
    if len(nomatch) > 0:
        build_logger.debug("Missing build parameters were found in build template!")
        build_logger.debug(nomatch)
        if exit_on_missing:
            exception_logger.debug("exit_on_missing=True in settings.cfg, exiting")
            sys.exit(1)
    else:
        build_logger.debug("All build parameters were filled, continuing")

# Write template to file
def write_template(script_file, script):
    with open(script_file, "w") as f:
        f.write(script)

