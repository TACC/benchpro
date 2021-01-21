
# System Imports
import sys

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    pass

# Local Imports
import exception
import logger

class init(object):
    def __init__(self, glob):
        self.glob = glob
        
    # Create db connection
    def connect(self):
        
        # Create db connection
        try:
            self.conn = psycopg2.connect(
                            dbname =    self.glob.stg['db_name'],
                            user =      self.glob.stg['db_user'],
                            host =      self.glob.stg['db_host'],
                            password =  self.glob.stg['db_passwd']
                            )

        except Exception as err:
            print ("psycopg2 connect() ERROR:", err)
            sys.exit(1)

        self.cur = self.conn.cursor()

    # Close db connection
    def disconnect(self):
        self.cur.close()
        self.conn.close()

    # Try to run query and return result
    def exec_query(self, statement):

        self.connect()

        try:
            self.cur.execute(statement)
            rows = self.cur.fetchall()
        except psycopg2.Error as e:
            print(e)
            sys.exit(1)

        self.disconnect()

        return rows

    # Try to run insert
    def exec_insert(self, statement):

        self.connect()

        try:
            self.cur.execute(statement)
            self.conn.commit()
        except psycopg2.Error as e:
            print(e)
            sys.exit(1)

        self.disconnect()

    # query application table for app_id
    def get_app_from_table(self, app_id):
        statement = "SELECT * from " + self.glob.stg['app_table'] + " WHERE app_id='"+app_id+"';"
        return self.exec_query(statement)

    # Query Application table for matching app_id
    def application_captured(self, app_id):

        rows = self.get_app_from_table(app_id)

        if len(rows) == 0:
            return False

        return True

    # Add this application to the database
    def capture_application(self, report_file):

        # Get application profile from bench_report
        insert_dict = self.glob.lib.report.read(report_file)['build']

        if insert_dict['jobid'] == "dry_run":
            print("Application build job was a dry run, skipping database presence check...")
            return

        # Do nothing if application is already capture to db
        if self.application_captured(insert_dict['app_id']):
            print("Application present in database.")
            return

        # Get key-value pairs from dict
        keys = ', '.join(insert_dict.keys())
        vals = ", ".join(["'" + str(v).replace("'", "").replace("\"", "") + "'" for v in insert_dict.values()])

        # Insert statement
        statement = "INSERT INTO " + self.glob.stg['app_table'] + " (" + keys + ") VALUES (" + vals + ");" 
        self.exec_insert(statement)
        print("Inserted new application instance '" + insert_dict['code'] + "' with app_id '" +\
                    insert_dict['app_id'] + "' into database")


    # Add this result to databse
    def capture_result(self, insert_dict):
       
        # Get key-value pairs from dict
        keys = ', '.join(insert_dict.keys())
        vals = ", ".join(["'" + str(v).replace("'", "").replace("\"", "") + "'" for v in insert_dict.values()])
 

        # Insert statement
        statement = "INSERT INTO " + self.glob.stg['result_table'] + " (" + keys + ") VALUES (" + vals + ");"
        self.exec_insert(statement)


    # Return fields of db table
    def get_table_fields(self, table):

        # Get columns names as tuple    
        query = "SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name='" + table + "';"

        col_names = self.exec_query(query)
        columns = []

        # Extract names from tuple
        for tup in col_names:
            columns += [ tup[0] ]

        # Pop default id field
        columns.remove('id')

        return columns



