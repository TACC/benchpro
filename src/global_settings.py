import configparser as cp
import os
import socket
from datetime import datetime

# General session constants
class init:

	user				= str(os.getlogin())
	hostname			= str(socket.gethostname())
	if ("." in hostname):
		hostname		= '.'.join(map(str, hostname.split('.')[0:2]))

	# Chicken & egg situation with 'sl' here - hardcoded 
	time_str			= datetime.now().strftime("%Y-%m-%d_%Hh%M")
	base_dir			= "/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[:-1])
	cwd				 	= os.getcwd()

	# settings.cfg handler
	settings_cfg 		= "settings.cfg"
	settings_parser 	= cp.RawConfigParser()
	settings_parser.read(base_dir + "/" + settings_cfg)

	# [common] section
	section	 			= 'common'
	dry_run				= settings_parser.getboolean(section,	'dry_run')
	exit_on_missing 	= settings_parser.getboolean(section,	'exit_on_missing')
	log_level 			= settings_parser.getint(section, 		'log_level')
	timeout				= settings_parser.getint(section,		'timeout')
	sl					= settings_parser.get(section,			'sl')

	# [config] section
	section				= 'config'
	configs_dir			= settings_parser.get(section,			'configs_dir')
	build_cfg_dir		= settings_parser.get(section,			'build_cfg_dir')  
	run_cfg_dir			= settings_parser.get(section,		  	'run_cfg_dir')
	sched_cfg_dir		= settings_parser.get(section,		  	'sched_cfg_dir')
	system_cfg_file		= settings_parser.get(section,		  	'system_cfg_file')
	arch_cfg_file		= settings_parser.get(section,		  	'arch_cfg_file')
	compile_cfg_file	= settings_parser.get(section,		  	'compile_cfg_file')

	# [template] section
	section 			= 'templates'
	template_dir		= settings_parser.get(section,		  	'template_dir')
	build_tmpl_dir		= settings_parser.get(section,		  	'build_tmpl_dir')
	sched_tmpl_dir		= settings_parser.get(section,		  	'sched_tmpl_dir')
	run_tmpl_dir		= settings_parser.get(section,		  	'run_tmpl_dir')
	compile_tmpl_file	= settings_parser.get(section,		  	'compile_tmpl_file')

	# [builder] section
	section 			= 'builder'
	use_default_paths	= settings_parser.getboolean(section,   'use_default_paths')
	overwrite			= settings_parser.getboolean(section,   'overwrite')
	build_dir			= settings_parser.get(section,		  	'build_dir')
	build_log_file		= settings_parser.get(section,   		'build_log_file')
	build_report_file	= settings_parser.get(section,		  	'build_report_file')

	# [bencher] section
	section				= 'bencher'
	dataset_dir			= settings_parser.get(section,   		'dataset_dir')
	run_log_file		= settings_parser.get(section,		  	'run_log_file')


	# Derived variables
	module_dir			= "modulefiles"
	default_build_path	= base_dir + sl + build_dir
	default_module_path	= default_build_path + sl + module_dir
