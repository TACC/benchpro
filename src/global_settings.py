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
	settings_parser 	= configparser.RawConfigParser(allow_no_value=True)
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
		topdir_env_var		= empty(settings_parser.get(section,		'topdir_env_var'))
		script_basedir		= empty(settings_parser.get(section,		'script_basedir'))

		# [config]
		section				= 'config'
		config_basedir		= empty(settings_parser.get(section,		'config_basedir'))
		build_cfg_dir		= empty(settings_parser.get(section,		'build_cfg_dir'))  
		bench_cfg_dir		= empty(settings_parser.get(section,	  	'bench_cfg_dir'))
		sched_cfg_dir		= empty(settings_parser.get(section,	  	'sched_cfg_dir'))
		system_cfg_file		= empty(settings_parser.get(section,	  	'system_cfg_file'))
		arch_cfg_file		= empty(settings_parser.get(section,	  	'arch_cfg_file'))
		compile_cfg_file	= empty(settings_parser.get(section,	  	'compile_cfg_file'))

		# [template]
		section 			= 'templates'
		template_basedir	= empty(settings_parser.get(section,	  	'template_basedir'))
		build_tmpl_dir		= empty(settings_parser.get(section,	  	'build_tmpl_dir'))
		sched_tmpl_dir		= empty(settings_parser.get(section,	  	'sched_tmpl_dir'))
		bench_tmpl_dir		= empty(settings_parser.get(section,	  	'bench_tmpl_dir'))
		compile_tmpl_file	= empty(settings_parser.get(section,	  	'compile_tmpl_file'))

		# [builder]
		section 			= 'builder'
		overwrite			= empty(settings_parser.getboolean(section, 'overwrite'))
		build_basedir		= empty(settings_parser.get(section,	  	'build_basedir'))
		build_subdir		= empty(settings_parser.get(section,		'build_subdir'))
		install_subdir		= empty(settings_parser.get(section,		'install_subdir'))
		build_log_file		= empty(settings_parser.get(section,   		'build_log_file'))
		build_report_file	= empty(settings_parser.get(section,	  	'build_report_file'))

		# [bencher]
		section				= 'bencher'
		benchmark_repo		= empty(settings_parser.get(section,   		'benchmark_repo'))
		bench_basedir		= empty(settings_parser.get(section,		'bench_basedir'))
		bench_log_file		= empty(settings_parser.get(section,	  	'bench_log_file'))
		bench_report_file   = empty(settings_parser.get(section,		'bench_report_file'))
		output_file			= empty(settings_parser.get(section,		'output_file'))

		# [results]
		section				= 'results'
		results_log_file	= empty(settings_parser.get(section,		'results_log_file'))

		# [database]
		section				= 'database'
		db_host				= empty(settings_parser.get(section,		'db_host'))
		db_name				= empty(settings_parser.get(section,		'db_name'))
		db_user				= empty(settings_parser.get(section,		'db_user'))
		db_passwd			= empty(settings_parser.get(section,		'db_passwd'))
		file_copy_handler   = empty(settings_parser.get(section,		'file_copy_handler'))
		user				= 		settings_parser.get(section,		'user')
		key					= 		settings_parser.get(section,		'key')
		django_static_dir	=		settings_parser.get(section,		'django_static_dir')
		server_dir			= 		settings_parser.get(section,		'server_dir')
		# [system]
		section 			= 'system'
		system_scripts_dir	= empty(settings_parser.get(section,		'system_scripts_dir'))
		system_utils_dir	= empty(settings_parser.get(section,		'system_utils_dir'))


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
	top_env			= topdir_env_var + sl
	module_basedir	= "modulefiles"
	build_path		= base_dir + sl + build_basedir
	bench_path		= base_dir + sl + bench_basedir
	config_path		= base_dir + sl + config_basedir
	template_path	= base_dir + sl + template_basedir
	script_path		= base_dir + sl + script_basedir
	module_path		= build_path + sl + module_basedir
	src_path		= base_dir + sl + "src"
	utils_path		= base_dir + sl + system_utils_dir

