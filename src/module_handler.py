# System Imports
import os
import shutil as su
import sys

# Local Imports
import src.common as common_funcs
import src.exception as exception

logger = gs = None

# Check inputs for module creation
def check_inputs(mod_dict, mod_path):

	if not mod_dict['system'] or not mod_dict['compiler'] or not mod_dict['mpi'] or not mod_dict["code"] or not mod_dict['version']:
		logger.debug("Missing full application definition:")
		logger.debug("----------------------------")
		logger.debug("System".ljust(10),   ":", mod_dict['system'])
		logger.debug("Compiler".ljust(10), ":", mod_dict['compiler'])
		logger.debug("MPI".ljust(10),	  ":", mod_dict['mpi'])
		logger.debug("Code".ljust(10),	 ":", mod_dict["code"])
		logger.debug("Version".ljust(10),  ":", mod_dict['version'])
		logger.debug("----------------------------")
		logger.debug("Exitting")
		sys.exit(1)

	# Check if module already exists
	if os.path.isfile(mod_path + gs.sl + mod_dict['version'] + ".lua"):

		if gs.overwrite:
			exception.print_warning(logger, "deleting old module in " + mod_path + " because 'overwrite=True' in settings.cfg")
			su.rmtree(mod_path)
			os.makedirs(mod_path)

		else:
			exception.error_and_quit(logger, "Module path already exists.")

# Copy template to target dir
def copy_mod_template(module_template, mod_file, module_use):
	#try:
	with open(mod_file, 'w') as out:
		with open(module_template, 'r') as inp:
				# Add custom module path if set in cfg
			if module_use:
				out.write("prepend_path( \"MODULEPATH\" , \"" + module_use + "\") \n")

			su.copyfileobj(inp, out)
	#except:
	#	exception.error_and_quit(logger, "Failed to copy " + module_template + " to " + mod_file)

# Replace <<<>>> vars in copied template
def populate_mod_template(module, mod_dict):
	# Get comma delimited list of build modules
	mod_dict['mods'] = ', '.join('"{0}"'.format(w) for w in mod_dict['mods'])
	# Get capitalized code name for env var
	mod_dict['caps_code'] = mod_dict['code'].upper().replace("-", "_")

	for key in mod_dict:
		logger.debug("replace " + "<<<" + key + ">>> with " + mod_dict[key])
		module = module.replace("<<<" + key + ">>>", mod_dict[key])
	return module

# Write module to file
def write_mod_file(module, mod_file):
	with open(mod_file, "w") as f:
		f.write(module)

# Make module for compiled appliation
def make_mod(general_opts, build_opts, mod_opts, settings, log_to_use):

	# Get global settings & logger obj
	global logger, gs
	logger = log_to_use
	gs = settings

	# Instantiate common_funcs
	common = common_funcs.init(gs)

	# Create combined module dict 
	mod_dict = {'mods': []}
	mod_dict['compiler'] = mod_opts['compiler']
	mod_dict['mpi'] = mod_opts['mpi']

	logger.debug("Creating module file for " + general_opts['code'])

	for mod in mod_opts:
		mod_dict['mods'] += [mod_opts[mod]]

	mod_dict.update(general_opts)
	mod_dict.update(build_opts)

	# Get module file path
	mod_path = gs.module_path + gs.sl + mod_dict['system'] + gs.sl + common.get_module_label(mod_dict['compiler']) + gs.sl + common.get_module_label(mod_dict['mpi']) + gs.sl + mod_dict['code'] + gs.sl + mod_dict['build_label']

	check_inputs(mod_dict, mod_path)
	# tmp module file name
	mod_file = "tmp." + mod_dict['version'] + ".lua"

	module_template = gs.template_path + gs.sl + gs.build_tmpl_dir + gs.sl + mod_dict['code'] + "-" + mod_dict['version'] + ".module"

	# Use generic module template if not found for this application
	if not os.path.exists(module_template):
		exception.print_warning(logger, "module template not found at " + common.rel_path(module_template))
		exception.print_warning(logger, "using a generic module template")
		module_template = "/".join(module_template.split("/")[:-1]) + gs.sl + "generic.module"

	# Copy base module template
	copy_mod_template(module_template, mod_file, general_opts['module_use'])
	module = open(mod_file).read()

	# Populuate template with config params
	module = populate_mod_template(module, mod_dict)
	# Test module template
	common.test_template(module_template, module, logger)
	# Write module template to file
	write_mod_file(module, mod_file)

	return mod_path, mod_file
