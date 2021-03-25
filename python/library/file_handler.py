# System imports
import glob as gb
import os

class init(object):
    def __init__(self, glob):
        self.glob = glob

    # Delete tmp build files if installation fails
    def remove_tmp_files(self):
        file_list = gb.glob(os.path.join(self.glob.basedir, 'tmp.*'))
        if file_list:
            for f in file_list:
                try:
                    os.remove(f)
                    self.glob.log.debug("Successfully removed tmp file "+f)
                except:
                    self.glob.log.debug("Failed to remove tmp file ", f)



