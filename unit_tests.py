import unittest

import src.common as common_funcs
import src.global_settings as global_settings
import src.logger as logger


glob = global_settings.settings()
common = common_funcs.init(glob)
glob.log = logger.start_logging("UNITTEST", "unittest" + "_" + glob.time_str + ".log", glob)

class TestBuilder(unittest.TestCase):

    def test_check_for_previous_install(self):
        self.assertEqual

    def generate_build_report(self):
        self.assertEqual

    def build_code(self):
        self.assertEqual

class TestCommon(unittest.TestCase):

    def test_rel_path(self):
        # Path empty
        self.assertEqual(self.common.rel_path(""),                           "")
        # Relative path
        self.assertEqual(self.common.rel_path("some/rel/path"),              "some/rel/path")
        # Absolute path
        self.assertEqual(self.common.rel_path(self.glob.stg['config_path']), "$TOPDIR/config")

    def test_find_exact(self):
        # File is path
        self.assertEqual(self.common.find_exact(self.glob.stg['module_path'] + self.glob.stg['sl'] + "builder.lua", self.glob.stg['module_path']),
                                                self.glob.stg['module_path'] + self.glob.stg['sl'] + "builder.lua")
        # Match found
        self.assertEqual(self.common.find_exact("slurm.template", self.glob.stg['template_path']), "/scratch/06280/mcawood/bench-framework/templates/sched/slurm.template")
        # No match found
        self.assertEqual(self.common.find_exact("somefile", self.glob.stg['module_path']), "")

    def test_find_partial(self):
        # File is path
        self.assertEqual(self.common.find_partial(self.glob.stg['module_path'] + self.glob.stg['sl'] + "builder.lua", self.glob.stg['module_path']),
                                                  self.glob.stg['module_path'] + self.glob.stg['sl'] + "builder.lua")
        # Multiple matches found
        self.assertEqual(self.common.find_partial("slurm", self.glob.stg['template_path']), "/scratch/06280/mcawood/bench-framework/templates/sched/slurm.template")
        # No matches found
        self.assertEqual(self.common.find_partial("gasdgasd", self.glob.stg['template_path']), "")

    def test_file_owner(self):
        self.assertEqual(self.common.file_owner("/etc/hosts"), "root")    
    
    def test_check_module_exists(self):
        # Lacking version
        self.assertEqual(self.common.check_module_exists("xalt", ""), "xalt/2.8")
        # Contains version
        self.assertEqual(self.common.check_module_exists("xalt/2.8", ""), "xalt/2.8")
        # Invalid module
        with self.assertRaises(SystemExit):
            self.common.check_module_exists("some_nonexistant_module", "")
        # Module use
        self.assertEqual(self.common.check_module_exists("mistral", "/scratch/01255/siliu/modulefiles/"), "mistral/2.13.5")

    def test_get_module_label(self):
        # Module contains slash
        self.assertEqual(self.common.get_module_label("intel/18.0.2"), "intel18")
        # No slash
        self.assertEqual(self.common.get_module_label("intel"), "intel")

    def test_get_subdirs(self):
        self.assertEqual(self.common.get_subdirs(self.glob.stg['config_path']), ['bench', 'build', 'sched'])

    def test_get_installed(self):
        self.assertIsNotNone(self.common.get_installed())

    def test_check_if_installed(self):
        self.assertEqual(self.common.check_if_installed('lammps'))
        



 #   def test_(self):
 #       self.assertEqual(self.common.())



if __name__ == '__main__':
    unittest.main()

