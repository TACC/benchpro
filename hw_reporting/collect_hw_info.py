import os
import sys
from datetime import datetime
import socket

DATE = datetime.now().strftime("%Y-%m-%d_%HH%M")

HOST="$(hostname -s).${TACC_SYSTEM:-unknown_sys}"

print(socket.gethostname())
