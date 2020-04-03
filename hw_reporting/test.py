import os
import sys
from datetime import datetime
import socket
import subprocess

# run() returns a CompletedProcess object if it was successful
# errors in the created process are raised here too
process = subprocess.run(['ls','-lha'], check=True, stdout=subprocess.PIPE, universal_newlines=True)
output = process.stdout

print(output)

