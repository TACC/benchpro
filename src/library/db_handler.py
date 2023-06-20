
# System Imports
import sys
from tabulate import tabulate
from typing import List

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    pass

class init(object):
    def __init__(self, glob):
        self.glob = glob
        
    # Create db connection
    def connect(self) -> None:
        
        # Create db connection
        try:
            self.conn = psycopg2.connect(
                            dbname =    self.glob.stg['db_name'],
                            user =      self.glob.stg['db_user'],
                            host =      self.glob.stg['db_host'],
                            password =  self.glob.stg['db_passwd']
                            )

        except Exception as err:
            self.glob.lib.msg.error(["psycopg2 connect() ERROR: ", err])

        self.cur = self.conn.cursor()

    # Close db connection
    def disconnect(self) -> None:
        self.cur.close()
        self.conn.close()

    # Try to run query and return result
    def exec_query(self, statement: str):

        self.connect()

        try:
            self.cur.execute(statement)
            rows = self.cur.fetchall()
        except psycopg2.Error as e:
            self.glob.lib.msg.error(e)

        self.disconnect()

        return rows

    # Try to run insert
    def exec_insert(self, statement: str) -> None:

        self.connect()

        try:
            self.cur.execute(statement)
            self.conn.commit()
        except psycopg2.Error as e:
            self.glob.lib.msg.error(e)

        self.disconnect()

    # query application table for app_id
    def get_app_from_table(self, app_id: str):
        statement = "SELECT * from " + self.glob.stg['app_table'] + " WHERE app_id='"+app_id+"';"
        return self.exec_query(statement)


    # Query Application table for matching app_id
    def app_in_table(self, app_id: str) -> bool:
        if self.glob.lib.db.get_app_from_table(app_id):
            return True
        return False


    # query result table for task_id
    def get_result_from_table(self, task_id: str):
        statement = "SELECT * from " + self.glob.stg['result_table'] + " WHERE task_id='"+str(task_id)+"';"
        return self.exec_query(statement)


    # Return True if task_id is present in results table
    def result_in_table(self, task_id: str) -> bool:
        if self.get_result_from_table(task_id):
            return True
        return False


    # Add this result to databse
    def insert_record(self, insert_dict: dict, table: str) -> None:
        # Get key-value pairs from dict
        keys = ', '.join(insert_dict.keys())
        vals = ", ".join(["'" + str(v).replace("'", "").replace("\"", "") + "'" for v in insert_dict.values()])
 
        # Insert statement
        statement = "INSERT INTO " + table + " (" + keys + ") VALUES (" + vals + ");"
        self.exec_insert(statement)

    # Return fields of db table
    def get_table_fields(self, table: str) -> List[str]:

        # Get columns names as tuple    
        query = "SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name='" + table + "';"

        col_names = self.exec_query(query)
        columns = []

        # Extract names from tuple
        for tup in col_names:
            columns += [ tup[0] ]

        return columns


    # Print app info from table
    def app_report(self, app_id: str = None) -> None:

        # Use cmdline arg if none provided
        app_id = app_id or self.glob.args.dbApp

        # Get app from table
        app = self.glob.lib.db.get_app_from_table(app_id)

        if not app:
            print("No application found matching app_id='" + self.glob.args.dbApp + "'")
            return

        app = app[0][0:]

        content =[  ["Code",            app[0]],
                    ["Version",         app[1]],
                    ["System",          app[2]],
                    ["Username",        app[12]],
                    ["Build date",      app[20]],
                    ["Job ID",          app[8]],
                    ["Module list",     app[5]],
                    ["Install path",    self.glob.lib.rel_path(app[23])],
                    ["App_ID",          app[9]]
                 ]

        print(tabulate(content, tablefmt="simple_outline", maxcolwidths=[None, 50]))


    def result_report(self, task_id: str = None) -> None:

        # Use cmdline arg if none provided
        task_id = task_id or self.glob.args.dbResult

        # Get result from table 
        result = self.glob.lib.db.get_result_from_table(task_id)

        if not result:
            print("No result found matching task_id='" + self.glob.args.dbResult + "'")
            return

        result = result[0][0:]

        # If result has associated app_id
        if result[-3]:
            self.app_report(result[-3])

        content =[  ["Dataset",         result[7]],
                    ["System",          result[1]],
                    ["Username",        result[0]],
                    ["Run date",        result[2]],
                    ["Job ID",          result[3]],
                    ["Working path",    "TBD"],
                    ["Nodes",           result[4]],
                    ["Ranks",           result[5]],
                    ["Threads",         result[6]],
                    ["GPUs",            "TBD"],
                    ["Nodelist",        result[11]],
                    ["Result",          str(result[8]) + " " + result[9]]
                 ]

        print(tabulate(content, tablefmt="simple_outline", maxcolwidths=[None, 50]))


    # Test if search field is valid in results/models.py
    def test_search_field(self, field: str) -> bool:

        if field in self.model_fields:
            return True

        else:
            self.glob.lib.msg.error(["'" + field + "' is not a valid search field.",
                                "Available fields:"] +
                                self.model_fields)


    # Parse comma-delmited list of search criteria, test keys and return SQL WHERE statement
    def parse_input_str(self, args: str) -> str:

        # No filter
        if not args or args == "all":
            return ";"

        select_str = ""
        for option in args.split(","):
            search = option.split('=')
            if not len(search) == 2:
                self.glob.lib.msg.error("Invalid query key-value pair: " + option)

            # Test search key is in db
            if self.glob.lib.db.test_search_field(search[0]):
                if select_str: select_str += " AND "
                else: select_str += " "

                # Handle time related query fields
                if search[0] in ['submit_time']:
                    select_str += "DATE(" + search[0] + ") = '" + search[1] + "'"
                else:
                    select_str += search[0] + "='" + search[1] + "'"

        return "WHERE " + select_str + ";"


    # List results from db
    def list_results(self, input_str: str = None) -> None:

        input_str = input_str or self.glob.args.dbList

        # Get fields in table
        self.model_fields = self.glob.lib.db.get_table_fields(self.glob.stg['result_table'])

        # Get sql query statement
        statement = "SELECT * FROM " + self.glob.stg['result_table'] + " " + self.parse_input_str(input_str)
        query_results = self.glob.lib.db.exec_query(statement)

        # If query produced no records
        if not query_results:
            print("No results found matching search criteria: '" + statement + "'")
            return 
        
        print()
        print("Running query:")
        print(statement)
        print(str(len(query_results)) + " results were found:")
        print()

        content = [["USER", "SYSTEM", "TASK_ID", "APP_ID", "DATASET", "RESULT"]]
        for result in query_results:
            content.append([result[0], 
                            result[1],
                            str(result[3]),
                            str(result[17]),
                            str(result[7]),
                            str(result[8])+" "+str(result[9])])

        print(tabulate(content, headers="firstrow", tablefmt="simple_outline"))

        # Export to csv
        if self.glob.args.export:
            csvFile = os.path.join(self.glob.cwd, "dbquery_"+ self.glob.stg['time_str'] + ".csv")
            print()
            print("Exporting to csv file: " + self.glob.lib.rel_path(csvFile))

            with open(csvFile, 'w') as outFile:
                wr = csv.writer(outFile, quoting=csv.QUOTE_ALL)
                wr.writerow(self.model_fields)
                wr.writerows(query_results)

            print("Done.")

