import MySQLdb

from connection import DATABASE
from connection import PASSWORD
from connection import USERNAME

def get_database_connection():

    db = MySQLdb.connect(
        host="localhost",
        user=PASSWORD,
        passwd=USERNAME,
        db=DATABASE)

    return db

