import sys
class TeeOutput:
    def __init__(self, *outputs):
        self.outputs = outputs

    def write(self, message):
        for output in self.outputs:
            output.write(message)
            output.flush()  # optional but good for real-time logging

    def flush(self):
        for output in self.outputs:
            output.flush()

def start_log(filename):
    terminal = sys.stdout

    # Open log file
    logfile = open(filename, "w")

    # Set tee output
    sys.stdout = TeeOutput(terminal, logfile)
