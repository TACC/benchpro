# System Imports
import configparser as cp
import os
import socket
from datetime import datetime

# General constants
class init:

    # Context variables
	user				= str(os.getlogin())
	hostname			= str(socket.gethostname())
	if ("." in hostname):
		hostname		= '.'.join(map(str, hostname.split('.')[0:2]))

	# Chicken & egg situation with 'sl' here - hardcoded 
	time_str			= datetime.now().strftime("%Y-%m-%d_%Hh%M")
	base_dir			= "/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[:-1])
	cwd				 	= os.getcwd()

	#----------------------------settings.cfg--------------------------------
	settings_cfg 		= "settings.cfg"
	settings_parser 	= cp.RawConfigParser()
	settings_parser.read(base_dir + "/" + settings_cfg)

	# [common]
	section	 			= 'common'
	dry_run				= settings_parser.getboolean(section,	'dry_run')
	exit_on_missing 	= settings_parser.getboolean(section,	'exit_on_missing')
	timeout				= settings_parser.getint(section,		'timeout')
	sl					= settings_parser.get(section,			'sl')
	tree_depth			= settings_parser.getint(section,       'tree_depth')

	# [config]
	section				= 'config'
	config_dir			= settings_parser.get(section,			'config_dir')
	build_cfg_dir		= settings_parser.get(section,			'build_cfg_dir')  
	run_cfg_dir			= settings_parser.get(section,		  	'run_cfg_dir')
	sched_cfg_dir		= settings_parser.get(section,		  	'sched_cfg_dir')
	system_cfg_file		= settings_parser.get(section,		  	'system_cfg_file')
	arch_cfg_file		= settings_parser.get(section,		  	'arch_cfg_file')
	compile_cfg_file	= settings_parser.get(section,		  	'compile_cfg_file')

	# [template]
	section 			= 'templates'
	template_dir		= settings_parser.get(section,		  	'template_dir')
	build_tmpl_dir		= settings_parser.get(section,		  	'build_tmpl_dir')
	sched_tmpl_dir		= settings_parser.get(section,		  	'sched_tmpl_dir')
	run_tmpl_dir		= settings_parser.get(section,		  	'run_tmpl_dir')
	compile_tmpl_file	= settings_parser.get(section,		  	'compile_tmpl_file')

	# [builder]
	section 			= 'builder'
	use_default_paths	= settings_parser.getboolean(section,   'use_default_paths')
	overwrite			= settings_parser.getboolean(section,   'overwrite')
	build_dir			= settings_parser.get(section,		  	'build_dir')
	build_log_file		= settings_parser.get(section,   		'build_log_file')
	build_report_file	= settings_parser.get(section,		  	'build_report_file')

	# [bencher]
	section				= 'bencher'
	dataset_dir			= settings_parser.get(section,   		'dataset_dir')
	run_log_file		= settings_parser.get(section,		  	'run_log_file')
    #---------------------------------------------------------------------------

	# Derived variables
	module_dir			= "modulefiles"
	build_path			= base_dir + sl + build_dir
	config_path			= base_dir + sl + config_dir
	template_path 		= base_dir + sl + template_dir
	module_path			= build_path + sl + module_dir
