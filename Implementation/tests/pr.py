import sys

class Logger(object):
    def __init__(self, logfile):
        self.terminal = sys.stdout
        self.log = open(logfile, "w", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)  # print to terminal
        self.log.write(message)       # write to file

    def flush(self):
        self.terminal.flush()
        self.log.flush()

sys.stdout = sys.stderr = Logger("output.log")
print("hefiflks;a")