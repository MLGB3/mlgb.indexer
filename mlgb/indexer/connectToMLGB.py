import MySQLdb

from connection import DATABASE
from connection import PASSWORD
from connection import USERNAME

def get_database_connection():
    import pdb;pdb.set_trace()
    db = MySQLdb.connect(
        host="localhost",
        user=USERNAME,
        passwd=PASSWORD,
        db=DATABASE)

    return db

