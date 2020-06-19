# System Imports
import configparser 
from datetime import datetime
import os
import socket
import sys

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
	settings_parser 	= configparser.RawConfigParser()
	settings_parser.read(base_dir + "/" + settings_cfg)

	def empty(key):
		if type(key) is str and not key :
			print("Missing key in settings.cfg, check the documentation.")
			sys.exit(1)
		else: return key

	try:
		# [common]
		section	 			= 'common'
		dry_run				= empty(settings_parser.getboolean(section,	'dry_run'))
		exit_on_missing 	= empty(settings_parser.getboolean(section,	'exit_on_missing'))
		timeout				= empty(settings_parser.getint(section,		'timeout'))
		sl					= empty(settings_parser.get(section,		'sl'))
		tree_depth			= empty(settings_parser.getint(section,	   	'tree_depth'))
		topdir_env_var		= empty(settings_parser.get(section,        'topdir_env_var'))

		# [config]
		section				= 'config'
		config_dir			= empty(settings_parser.get(section,		'config_dir'))
		build_cfg_dir		= empty(settings_parser.get(section,		'build_cfg_dir'))  
		bench_cfg_dir		= empty(settings_parser.get(section,	  	'bench_cfg_dir'))
		sched_cfg_dir		= empty(settings_parser.get(section,	  	'sched_cfg_dir'))
		system_cfg_file		= empty(settings_parser.get(section,	  	'system_cfg_file'))
		arch_cfg_file		= empty(settings_parser.get(section,	  	'arch_cfg_file'))
		compile_cfg_file	= empty(settings_parser.get(section,	  	'compile_cfg_file'))

		# [template]
		section 			= 'templates'
		template_dir		= empty(settings_parser.get(section,	  	'template_dir'))
		build_tmpl_dir		= empty(settings_parser.get(section,	  	'build_tmpl_dir'))
		sched_tmpl_dir		= empty(settings_parser.get(section,	  	'sched_tmpl_dir'))
		bench_tmpl_dir		= empty(settings_parser.get(section,	  	'bench_tmpl_dir'))
		compile_tmpl_file	= empty(settings_parser.get(section,	  	'compile_tmpl_file'))

		# [builder]
		section 			= 'builder'
		overwrite			= empty(settings_parser.getboolean(section, 'overwrite'))
		build_dir			= empty(settings_parser.get(section,	  	'build_dir'))
		build_log_file		= empty(settings_parser.get(section,   		'build_log_file'))
		build_report_file	= empty(settings_parser.get(section,	  	'build_report_file'))

		# [bencher]
		section				= 'bencher'
		benchmark_repo		= empty(settings_parser.get(section,   		'benchmark_repo'))
		bench_dir			= empty(settings_parser.get(section,        'bench_dir'))
		bench_log_file		= empty(settings_parser.get(section,	  	'bench_log_file'))
		bench_report_file   = empty(settings_parser.get(section,        'bench_report_file'))
		output_file			= empty(settings_parser.get(section,        'output_file'))

		# [results]
		section             = 'results'
		results_log_file	= empty(settings_parser.get(section,        'results_log_file'))

		# [database]
		section             = 'database'
		db_host				= empty(settings_parser.get(section,        'db_host'))
		db_name             = empty(settings_parser.get(section,        'db_name'))
		db_user             = empty(settings_parser.get(section,        'db_user'))
		db_passwd           = empty(settings_parser.get(section,        'db_passwd'))

		# [hw_info]
		section 			= 'hw_info'
		utils_dir			= empty(settings_parser.get(section,	  	'utils_dir'))

	except configparser.NoSectionError as e:
		print("Missing [section] in settings.cfg, check the documentation.")
		print(e)
		sys.exit(1)

	except Exception as e:# configparser.Error as e:
		print("Error parsing settings.cfg, check the documentation.")
		print(e)
		sys.exit(1)
	#---------------------------------------------------------------------------

	# Derived variables
	top_env         = topdir_env_var + sl
	module_dir		= "modulefiles"
	build_path		= base_dir + sl + build_dir
	bench_path		= base_dir + sl + bench_dir
	config_path		= base_dir + sl + config_dir
	template_path	= base_dir + sl + template_dir
	module_path		= build_path + sl + module_dir
	src_path		= base_dir + sl + "src"
	utils_path		= base_dir + sl + utils_dir

