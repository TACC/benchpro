# System Imports
import os
import sys
from packaging import version
from typing import List

class init(object):
    def __init__(self, glob):
            self.glob = glob

    #---------------STARTUP VERSION CHECKING----------------------

    # Get minimum compatible version from defaults.ini
    def min_version(self):
        return version.parse(self.glob.stg['minimum_compatible'])


    # Extract last run version number from $BP_HOME/.version file
    def user_version(self):
        version_file = os.path.join(self.glob.ev['BP_HOME'], ".version")
        if not os.path.isfile(version_file):
            self.write_version()

        self.glob.user_version = self.glob.lib.files.read(version_file)[0].strip()
        return version.parse(self.glob.user_version)


    def write_version(self) -> None:
        version_file = os.path.join(self.glob.ev['BP_HOME'], ".version")
        current_version = os.environ.get("BPS_VERSION")
        self.glob.lib.files.write_list_to_file([current_version], version_file)


    def old_files(self):

        file_list = ['settings.ini']

        for old_file in file_list:
            if os.path.isfile(os.path.join(self.glob.ev['BP_HOME'], old_file)):
                self.glob.lib.msg.error(["BenchPRO has detected old and imcompatible files in $BP_HOME:",
                                        old_file,
                                        "You may need to backup your .cfg and .template files and start fresh with:",
                                        "bp --purge",
                                        "You can disable this warning with 'bps check_version=False'",
                                        "Or delete the offending files and proceed."])


    def compatible(self) -> bool:
        if self.min_version() <= self.user_version():
            return True
        return False


    def check(self) -> None:

        # Skip version check if purging 
        if not self.glob.args.purge:
            compatible = self.compatible()
            if self.glob.stg['check_version']:
                self.old_files()
                if compatible:
                    self.glob.lib.msg.log("User version is compatible")
                    return

                self.glob.lib.msg.error(["BenchPRO minimum compatible version: " + self.glob.stg['minimum_compatible'],
                                        "Your last run version: " + self.glob.user_version,
                                        "You may need to modify your input files.",
                                        "Delete $BP_HOME/.version when ready to proceed."])

            else:
                if not compatible:
                    self.glob.lib.msg.warn("Your BenchPRO files may be out-of-date, continuing cautiously...")

    #---------------REPORT VERSION CHECKING----------------------

    def report_metadata(self) -> List[str]:
        head_list = [   "[metadata]",
                        "benchpro_version  = " + self.glob.ev['BPS_VERSION_STR'],
                        "format_version    = " + self.glob.stg['report_format']
                    ]
        return head_list


    def compat_report(self, report) -> bool:

        # Old file - no version header
        if not 'metadata' in report:
            return False

        report_version = version.parse(report['metadata']['format_version'])
        required_version = version.parse(self.glob.stg['report_format'])

        if report_version >= required_version:
            return True
        return False
