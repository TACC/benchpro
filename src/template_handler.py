# System Imports
import shutil as su
import sys

# Local Imports
import src.common as common_funcs
import src.exception as exception

logger = gs = ''

# Combines list of input templates to single script file
def construct_template(input_templates, script_file):
	with open(script_file, 'wb') as out:
		for f in input_templates:
			logger.debug("Ingesting template file " + f)
			with open(f, 'rb') as fd:
				su.copyfileobj(fd, out)

# Contextualizes template script with variables from a list of config dicts
def populate_template(input_cfgs, script_file):
	logger.debug("Populating template file " + script_file)
	script = open(script_file).read()
	# For each config dict
	for cfg in input_cfgs:
		# For each key, find and replace <<<key>>> in template file
		for key in cfg:
			logger.debug("replacing " + "<<<" + str(key) + ">>> with " + str(cfg[key]))
			script = script.replace("<<<" + str(key) + ">>>", str(cfg[key]))
	return script

# Combine template files and populate
def generate_template(input_cfgs, input_templates, script_file, settings, log_to_use):

	# Get global settings & logger obj
	global logger, gs
	logger = log_to_use
	gs = settings

	# Instantiate common_funcs
	common = common_funcs.init(gs)

	# Take multiple input template files and combine them to generate unpopulated script
	construct_template(input_templates, script_file)
	# Take multiple config dicts and populate script template
	script = populate_template(input_cfgs, script_file)
	# Test for missing parameters
	common.test_template(script_file, script, logger)
	# Read populated script to file
	with open(script_file, "w") as f:
		f.write(script)
