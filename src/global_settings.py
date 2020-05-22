import configparser as cp
import os
import socket
from datetime import datetime

# General session constants


class init:
	sl = "/"

	user = str(os.getlogin())
	hostname = str(socket.gethostname())
	if ("." in hostname):
		hostname = '.'.join(map(str, hostname.split('.')[0:2]))

	time_str = datetime.now().strftime("%Y-%m-%d_%Hh%M")
	base_dir = sl.join(os.path.dirname(
		os.path.abspath(__file__)).split('/')[:-1])
	cwd = os.getcwd()

	timeout = 5

	# settings.cfg handler
	settings_cfg = "settings.cfg"
	settings_parser = cp.RawConfigParser()
	settings_parser.read(base_dir + sl + settings_cfg)

	common_section = "common"
	dry_run = settings_parser.getboolean(common_section,   "dry_run")
	exit_on_missing = settings_parser.getboolean(
		common_section,   "exit_on_missing")
	log_level = settings_parser.getint(common_section,   "log_level")

	builder_section = "builder"
	use_default_paths = settings_parser.getboolean(
		builder_section,   "use_default_paths")
	overwrite = settings_parser.getboolean(builder_section,   "overwrite")
	build_log_file = settings_parser.get(builder_section,   "build_log_file")

	bencher_section = "bencher"
	run_log_file = settings_parser.get(bencher_section,   "run_log_file")

	build_dir = "build"

	# Config file handling constants
	configs_dir = "config"
	build_cfg_dir = "build"
	run_cfg_dir = "run"
	sched_cfg_dir = "sched"
	system_cfg_file = "system.cfg"
	arch_cfg_file = "architecture_defaults.cfg"

	# Template file handing constants
	template_dir = "templates"
	build_tmpl_dir = "build"
	sched_tmpl_dir = "sched"
	run_tmpl_dir = "run"
