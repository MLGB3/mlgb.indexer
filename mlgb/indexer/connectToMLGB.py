import MySQLdb
##=====================================================================================

def get_database_connection(): #{

  db = MySQLdb.connect( host="localhost",  # your host, usually localhost
                        user="mlgbAdmin",  # your username
                        passwd="blessing", # your password
                        db="mlgb")         # name of the database
  return db
#}
##=====================================================================================
