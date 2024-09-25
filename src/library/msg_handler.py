
# System imports
import copy
import os
import random
import signal
import subprocess
import sys
import time
from tabulate import tabulate
import textwrap
from typing import List

from src.modules import Result


class init(object):


    # Catch user interrupt
    def signal_handler(self, sig, frame):

        # Print raw error in dev mode
        if self.glob.dev_mode:
            print(sig)
        # Send to log
        elif self.glob.log:
            self.high('    Writing to log, cleaning up and quitting...')
            self.glob.lib.msg.log("Caught user interrupt, exitting.")
        else:
            print("    Quitting.")

        # Remove files
        self.glob.lib.files.rollback()
        sys.exit(1)


    def __init__(self, glob):
        self.glob = glob
        # Init interrupt handler
        signal.signal(signal.SIGINT, self.signal_handler) 


    # Convert strings to lists: str -> [str], list -> list
    def listify(self, message: str):
        if not isinstance(message, list):
            return [message]
        return message


    # Write message to log 
    def log(self, message: str):
        # If initialized
        if self.glob.log:
            self.glob.log.debug(message)


    # Log and print to stdout
    def log_and_print(self, message, priority):
        message = self.listify(message)

        # Print to stdout if msg priority meets verbosity level
        print_to_stdout = self.glob.stg['verbosity'] >= priority

        wrapper = textwrap.TextWrapper(self.glob.stg['width'])
        # For each line of message
        for line in message:
            if line:

                # Cast to line contents string
                if type(line) == subprocess.CalledProcessError:
                    line = line.output

                # Write to log 
                self.log(line)
                # Print to stdout if debug=True or high priority message
                if print_to_stdout:
                    word_list = wrapper.wrap(text=line)
                    for elem in word_list:
                        print(elem)

        # Print line break for multiple 
        if len(message) > 1 and print_to_stdout:
            print()


    # High priority message, nonconditional
    def high(self, message: str):
        self.log_and_print(message, 3)   


    # Low priority message, conditional on debug=True
    def low(self, message: str):
        self.log_and_print(message, 4)


    # Print message to log and stdout then continue
    def warn(self, message: str):
        self.log_and_print([self.glob.warning] + self.listify(message), 2)


    def exit(self, message: str, failed: bool = False) -> None:
        self.log_and_print(message, 1)

        if failed:
            # Clean tmp files
            if self.glob.stg['clean_on_fail']:
                self.log_and_print("Cleaning up tmp files...", 1)
                self.glob.lib.files.rollback()

                self.log_and_print(["Quitting", ""], 1)
                sys.exit(1)

        sys.exit(0)


    # Print message to log and stdout then quit
    def error(self, message: str):
        self.exit(self.listify(message), True)


    def success(self, message: str):
        self.exit(self.listify(message), False)


    # Print heading text in bold
    def heading(self, message: str):
        message = self.listify(message)

        message[0] = self.glob.bold + message[0]
        message[-1] = message[-1] + self.glob.end

        self.log_and_print([""] + message, 2)


    # Print section break
    def brk(self):
        self.log_and_print(["---------------------------", ""],3)


    # Force output regardless of msg priority settings
    def force(self, message: str):
        print(message)


    # Get list of uncaptured results and print note to user
    def new_results(self):
    
        if not self.glob.stg['skip_result_check']:

            self.log_and_print(["Checking for uncaptured results..."], 4)
            # Uncaptured results + job complete
            complete_results = self.glob.lib.result.get_completed()
            if complete_results:
                self.log_and_print([self.glob.note,
                                    "There are " + str(len(complete_results)) + " uncaptured results found in " + 
                                    self.glob.lib.rel_path(self.glob.stg['pending_path']),
                                    "Run 'benchpro --capture' to send to database."], 4)
            else:
                self.log_and_print(["No new results found.",
                                    ""], 4)


    # Print message about application exe file
    def exe_check(self, exe: str, search_path: str):   
        # Check if it exists
        exe_exists = self.glob.lib.files.exists(exe, search_path)

        if exe_exists:
            self.low(["Application executable found in:",
                            ">  " + self.glob.lib.rel_path(search_path)])
        else:
            self.error("failed to locate application executable '" + exe + " 'in " + self.glob.lib.rel_path(search_path))


    # Print last 20 lines of file
    def print_file_tail(self, file_path: str):

        # File exists
        if not os.path.isfile(file_path):
            self.glob.lib.msg.error("File not found: " + self.glob.lib.rel_path(file_path))

        print()
        print("=====> " + self.glob.lib.rel_path(file_path) + " <=====")

        # Print last 20 lines
        with open(file_path, 'r') as fp:
                lines = fp.readlines()
                [print(x.strip()) for x in lines[max(-15, (len(lines)*-1)):]]

        print("=====> " + self.glob.lib.rel_path(file_path) + " <=====")


    # Print the list of installed applications
    def print_app_table(self, table_contents=None):

        # If sent empty list, print everything
        if not table_contents:
            if not self.glob.installed_apps_list:
                self.glob.lib.set_installed_apps()
            table_contents = self.glob.installed_apps_list

            if not table_contents:
                self.glob.lib.msg.success("No applications installed.")

        table = []
        col_tags = ['app_id',
                    'task_id',
                    'code',
                    'version',
                    'submit_time',
                    'build_label',
                    'status']

        num_cols = len(col_tags)

        # Handle non existant key-values in report file (backwards compatibility)
        for record in table_contents:

            # Make elems print friendly
            record["submit_time"] = record["submit_time"].split(".")[0]


            row = ["-"] * num_cols

            # Get cell value, if it exists
            for idx in range(num_cols):
                try:
                    row[idx] = str(record[col_tags[idx]])
                except:
                    pass

            # Add row to table
            table.append(row) 
 
        table.sort(key=lambda x: x[4])

        # Add header now
        table = [[  "APP_ID",
                    "TASK_ID",
                    "CODE",
                    "VERSION",
                    "SUBMIT_TIME",
                    "BUILD_LABEL",
                    "STATUS"]] + \
                    table 

        print(tabulate(table, headers="firstrow", tablefmt="simple_outline"))


    def get_table_row(self, record: Result) -> List[str]:
        row = []
        col_tags = [['bench', 'result_id'], ['bench', 'task_id'],
                    ['bench', 'bench_label'], ['bench', 'submit_time'],
                    ['bench', 'dataset'], ['bench', 'nodes']]

        for column in col_tags:
            sect = column[0]
            key = column[1]
            # Get valid field from report, or field remains '-'
            try:
                row.append(record.report[sect][key])
            except:
                row.append("-")

        # Add result 
        if record.value:
            row.append(str(record.value) + " " + record.unit)

        elif record.status:
            row.append(record.status)
        else:
            row.append("-")

        return row


    # Print result list to table
    def print_result_table(self, table_contents: List[Result] = None) -> None:

        table_contents = table_contents or self.glob.lib.result.collect_reports(self.glob.args.listResults)

        if not table_contents:
            self.glob.lib.msg.error("No results found.")

        num_cols = 7
        table = []

        self.glob.lib.msg.high("Collecting " + str(len(table_contents)) + " results...")

        # Populate each row
        for record in table_contents:
            record.process()
            row = self.get_table_row(record)
            table.append(row)

        table.sort(key=lambda x: x[3])

        table = [[  "RESULT_ID",
                    "TASK_ID",
                    "BENCH_LABEL",
                    "SUBMIT_TIME",
                    "DATASET",
                    "NODES",
                    "RESULT"]] +\
                    table

        print(tabulate(table, headers="firstrow", tablefmt="simple_outline"))


    # Print timing
    def wait(self):
        for i in range(self.glob.stg['timeout']):
            time.sleep(1)
            print(".", end='', flush=True)
        print()


    # Print random hint
    def print_hint(self):

        if self.glob.stg['print_hint'] and self.glob.stg['verbosity'] >= 3:
            with open(os.path.join(self.glob.stg['site_resource_path'], "hints.txt")) as hint_file:
                hints = hint_file.readlines()

            hint = "HINT: " + random.choice(hints)

            wrapper = textwrap.TextWrapper(min(80, self.glob.stg['width']))
            word_list = wrapper.wrap(text=hint)
            for elem in word_list:
                print(elem)
            print()

    
    # Get y/n from user
    def get_yes(self) -> bool:

        # Assume True if not in interactive mode
        if not self.glob.stg['interactive']:
            return True

        if input("Are you sure? [Y/n] \n") in ["Y", "y", "yes", "Yes", "1"]:
            return True
        return False

    # Quit if prompt != Yes 
    def prompt(self) -> None:
        if not self.get_yes():
            self.exit("Quitting.")

