from tester._clients.das import DAS  # Import DAS class
from time import sleep
import sys
d = DAS('192.168.1.90')  # Create DAS instance and store it in variable b
d.connect()
sys.stdout.write("########## Script stdout 1\n")
for _ in range(10):
    d.main = 1
    sleep(0.5)
    d.main = 0
    sleep(0.5)
d.disconnect()
sleep(3)