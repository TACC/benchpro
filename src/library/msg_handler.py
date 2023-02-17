
# System imports
import copy
import os
import random
import signal
import sys
import time

import src.library.misc_handler       as misc_handler

class init(object):

    # Catch user interrupt
    def signal_handler(self, sig, frame):

        # Print raw error in dev mode
        if self.glob.dev_mode:
            print(sig)
        # Send to log
        elif self.glob.log:
            self.high('    Writing to log, cleaning up and aborting...')
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

        self.misc     = misc_handler.init(self.glob) 

    # Convert strings to lists: str -> [str], list -> list
    def listify(self, message):
        if not isinstance(message, list):
            return [message]
        return message
   
    # Write message to log 
    def log(self, message):
        # If initialized
        if self.glob.log:
            self.glob.log.debug(message)

    # Log and print to stdout
    def log_and_print(self, message, priority):
        message = self.listify(message)

        # For each line of message
        for line in message:
            if line:
                # Write to log 
                self.log(line)
                # Print to stdout if debug=True or high priority message
                if self.glob.stg['debug'] or priority: 
                    print(line)

        # Print line break for multiple 
        if len(message) > 1 and (self.glob.stg['debug'] or priority):
            print()

    # High priority message, nonconditional
    def high(self, message):
        self.log_and_print(message, True)   

    # Low priority message, conditional on debug=True
    def low(self, message):
        self.log_and_print(message, False)            

    # Print message to log and stdout then continue
    def warn(self, message):
        self.log_and_print([self.glob.warning] + self.listify(message), True)

    def exit(self, message, failed):
        self.log_and_print(message, True)

        if failed:
            # Clean tmp files
            if self.glob.stg['clean_on_fail']:
                self.log_and_print("Cleaning up tmp files...", True)
                self.glob.lib.files.rollback()

                self.log_and_print(["Quitting", ""], True)
                sys.exit(1)

        sys.exit(0)

    # Print message to log and stdout then quit
    def error(self, message):
        self.exit(self.listify(message), True)

    def success(self, message):
        self.exit(self.listify(message), False)

    # Print heading text in bold
    def heading(self, message):
        message = self.listify(message)

        message[0] = self.glob.bold + message[0]
        message[-1] = message[-1] + self.glob.end

        self.log_and_print([""] + message, True)

    # Print section break
    def brk(self):
        print("---------------------------")
        print()

    # Get list of uncaptured results and print note to user
    def new_results(self):
    
        if not self.glob.stg['skip_result_check']:

            self.log_and_print(["Checking for uncaptured results..."], False)
            # Uncaptured results + job complete
            complete_results = self.glob.lib.get_completed_results(self.glob.lib.get_pending_results(), True)
            if complete_results:
                self.log_and_print([self.glob.note,
                                    "There are " + str(len(complete_results)) + " uncaptured results found in " + 
                                    self.glob.lib.rel_path(self.glob.stg['pending_path']),
                                    "Run 'benchpro --capture' to send to database."], False)
            else:
                self.log_and_print(["No new results found.",
                                    ""], False)


    # Print message about application exe file
    def exe_check(self, exe, search_path):   
        # Check if it exists
        exe_exists = self.glob.lib.files.exists(exe, search_path)

        if exe_exists:
            self.low(["Application executable found in:",
                            ">  " + self.glob.lib.rel_path(search_path)])
        else:
            self.error("failed to locate application executable '" + exe + "'in " + self.glob.lib.rel_path(search_path))

    # Print last 20 lines of file
    def print_file_tail(self, file_path):

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
        col_tags = ['task_id',
                    'username',
                    'code',
                    'version',
                    'submit_time',
                    'build_label',
                    'status',
                    'rel_path']

        num_cols = len(col_tags)

        # Handle non existant key-values in report file (backwards compatibility)
        for record in table_contents:

            # Make elems print friendly
            record["rel_path"] = self.glob.lib.rel_path(record["path"])
            record["submit_time"] = record["submit_time"].split(".")[0]


            row = ["NULL"] * num_cols

            # Get cell value, if it exists
            for idx in range(num_cols):
                try:
                    row[idx] = str(record[col_tags[idx]])
                except:
                    pass

            # Add row to table
            table.append(row) 
        
        # Add header now
        table = [[   "TASK ID",
                    "OWNER",
                    "CODE",
                    "VERSION",
                    "BUILD DATE",
                    "LABEL",
                    "\x1b[0;37mSTATUS\x1b[0m",
                    "PATH"]] + \
                    table 

        # Check header has same num cols and content
        if len(table[0]) != (len(table[1])):
            self.glob.lib.msg.error("Mismatched number of table columns.")

        # Get max length of each table column (for spacing)
        col_len = [0] * num_cols
        col_chars = [0] * num_cols
        

        chars_left = self.glob.session['columns'] - 10
        max_col_chars = 25
        last_field_len = 0

        # Iterate over table columns
        for i in range(num_cols):
            # Iterate over table rows
            for row in table:
                # Find maximum string length for column across all rows

                cell_len = len(str(row[i]))
                if cell_len > col_chars[i]:
                    chars = min(col_len[i], max_col_chars)
                    col_chars[i] = chars
                    col_len[i] = max(col_len[i], cell_len)

            chars_left -= chars

        chars_left += last_field_len
        col_chars[-1] = max(5, min(col_len[-1], (chars_left+10))) #min(chars_left, col_len[-1]+15)


        col_chars = [10, 10, 10, 10, 18, 12, 20]
        tot_chars = sum(col_chars)
        col_chars.append(self.glob.session['columns'] - tot_chars - 30)

        # Buffer each column 2 chars
        padding = [i + 2 for i in col_chars]

        # Print contents
        for row in range(0,len(table)): 

            print("| ", end='')
            for column in range(num_cols):
                print(  str(table[row][column])[:col_chars[column]].ljust(padding[column]) + \
                        self.glob.end + "| ", end='')
            print()

    # Print timing
    def wait(self):
        print(".", end='')
        for i in range(self.glob.stg['timeout']):
            time.sleep(1)
            print(".", end='')
        print()

    # Print random hint
    def print_hint(self):


        if self.glob.stg['print_hint']:
            with open(os.path.join(self.glob.stg['site_resource_path'], "hints.txt")) as hint_file:
                hints = hint_file.readlines()

            hint = random.choice(hints)
            print("HINT: " + hint)

