
import os
import sys

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    pass

# Local Imports
import src.logger          as logger
from src.modules import Result


class init(object):

    def __init__(self, glob):
        self.glob = glob


    # Create .capture-complete file in result dir
    def success(self, result: Result) -> None:
       self.glob.lib.msg.low("Successfully captured result in " + self.glob.lib.rel_path(result.path))
       self.glob.lib.files.move_to_archive(result.path, self.glob.stg['captured_path'])


    #Create .capture-failed file in result dir
    def failed(self, msg: str, result: Result) -> None:
        self.glob.lib.msg.high(msg + self.glob.lib.rel_path(result.path))
        # Move failed result to subdir if 'move_failed_result' is set
        if self.glob.stg['move_failed_result']:
            self.glob.lib.files.move_to_archive(result.path, self.glob.stg['failed_path'])


    # Look for results and send them to db
    def results(self) -> None:

        # Start logger
        logger.start_logging("CAPTURE", self.glob.stg['results_log_file'] + "_" + self.glob.stg['time_str'] + ".log", self.glob)

        # Get list of results in $BP_RESULTS/complete with a COMPLETE job state
        Result.glob = self.glob
        complete_results_list = self.glob.lib.result.collect_reports("complete")
        num_results = len(complete_results_list)

        # No outstanding results
        if not complete_results_list:
            self.glob.lib.msg.error("No new results found in " + self.glob.lib.rel_path(self.glob.stg['pending_path']))

        self.glob.lib.msg.log("Capturing " + str(num_results) + " results")
        captured = 0
        
        # Print heading
        if num_results == 1: self.glob.lib.msg.heading("Starting capture for " + str(num_results) + " new result.")
        else: self.glob.lib.msg.heading("Starting capture for " + str(num_results) + " new results.")

        for result in complete_results_list:

            self.glob.lib.msg.low("Capturing " + result.label)
            # Capture application profile for this result to db if not already present
            self.glob.lib.capture.application(result)

            # If unable to get valid result, skipping this result
            if not result.value:
                if result.dry_run:
                    self.glob.lib.capture.failed("Skipping this dryrun result in ", result)
                else:
                    self.glob.lib.capture.failed("Failed to capture result in ", result)
                continue

            self.glob.lib.msg.low("Result: " + str(result.value) + " " + result.unit)

            # 1. Check not present
            if self.glob.lib.db.result_in_table(result.task_id):
                self.glob.lib.msg.warn("Result already in database, skipping.")
                continue

            # 2. Get insert dict
            insert_dict = self.glob.lib.capture.get_insert_dict(result)
            # If insert_dict failed
            if not insert_dict:
                self.glob.lib.capture.failed("Failed to capture result in ", result)
                continue

            # 3. Insert result into db
            self.glob.lib.msg.log("Inserting into database...")
            self.glob.lib.db.insert_record(insert_dict, self.glob.stg['result_table'])

            # 4. Copy files to collection dir
            self.glob.lib.msg.log("Sending provenance data...")
            #self.glob.lib.files.copy_prov_data([result.result['output_file']], result.path, insert_dict['resource_path'])
            self.glob.lib.files.copy_prov_data(result, insert_dict['resource_path'])

            # 4. Touch .capture-complete file
            self.glob.lib.capture.success(result)
            captured += 1

        self.glob.lib.msg.high(["", "Done. " + str(captured) + " results sucessfully captured"])


    # Generate dict for postgresql
    def get_insert_dict(self, result: Result) -> dict:

        insert_dict = {}

        insert_dict['username']         = result.build['username']
        insert_dict['system']           = result.build['system']
        insert_dict['submit_time']      = result.get_submit_time()
        insert_dict['elapsed_time']     = result.get_elapsed_secs()
        insert_dict['end_time']         = result.get_end_time()
        insert_dict['capture_time']     = result.get_capture_time()
        insert_dict['description']      = result.result['description']
        insert_dict['exec_mode']        = result.bench['exec_mode']
        insert_dict['task_id']          = str(result.task_id)
        insert_dict['job_status']       = result.status
        insert_dict['nodelist']         = result.get_nodelist()
        insert_dict['nodes']            = result.bench['nodes']
        insert_dict['ranks']            = result.bench['ranks']
        insert_dict['threads']          = result.bench['threads']
        insert_dict['gpus']             = result.bench['gpus']
        insert_dict['dataset']          = result.bench['dataset']
        insert_dict['result']           = str(result.value)
        insert_dict['result_unit']      = result.unit
        insert_dict['resource_path']    = os.path.join(insert_dict['username'], insert_dict['system'], insert_dict['task_id'])
        insert_dict['app_id']           = result.app_id
        insert_dict['result_id']        = result.result_id


        # Remove None values
        insert_fields = list(insert_dict.keys())

        for key in insert_fields:
            if insert_dict[key] is None:
                insert_dict.pop(key)

        model_fields = self.glob.lib.db.get_table_fields(self.glob.stg['result_table'])
        insert_fields = insert_dict.keys()

        for key in insert_fields:

            # Remove key from model list
            if key in model_fields:
                model_fields.remove(key)
            # Error if trying to insert field not in model
            else:
                self.glob.lib.msg.error("Trying to insert into field '" + key + \
                                            "' not present in results table '" + self.glob.stg['result_table'] + "'")

        return insert_dict


    # Add this application to the database
    def application(self, result: Result) -> None:

        # Get application profile from bench_report
        insert_dict = result.build

        # Abort if no application needed
        if not insert_dict:
            self.glob.lib.msg.low("This benchmark has no application dependency, skipping database presence check...")
            return

        # Abort if dry_run
        if "dry" in insert_dict['task_id']:
            self.glob.lib.msg.low("Application build job was a dry run, skipping database presence check...")
            return

        # Error if key is missing
        if not 'app_id' in insert_dict.keys():
            self.glob.lib.msg.error("key 'app_id' not present in report " + self.glob.lib.rel_path(report_file))

        # Do nothing if application is already capture to db
        if self.glob.lib.db.app_in_table(insert_dict['app_id']):
            self.glob.lib.msg.log("Application present in database.")
            return

        # Handle Null values
        insert_dict = {k: " " if not v else v for k, v in insert_dict.items() }

        self.glob.lib.db.insert_record(insert_dict, self.glob.stg['app_table'])

        self.glob.lib.msg.low("Inserted new application instance '" + insert_dict['code'] + "' with app_id '" +\
                    insert_dict['app_id'] + "' into database")

