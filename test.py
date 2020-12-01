import psycopg2
from psycopg2 import sql
import src.global_settings as global_settings

glob = global_settings.settings()

try:
    conn = psycopg2.connect(
        dbname =    glob.stg['db_name'],
        user =      glob.stg['db_user'],
        host =      glob.stg['db_host'],
        password =  glob.stg['db_passwd']
    )
    cur = conn.cursor()
except psycopg2.Error as e:
    print(e)
    exception.error_and_quit(glob.log, "Unable to connect to database")


cur.execute("SELECT * FROM " + glob.stg['table_name'] + " WHERE DATE(results_result.submit_time) = '2020-11-24'" + ";")
rows = cur.fetchall()


print(len(rows))
