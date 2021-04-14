import mysql.connector
from mysql.connector import Error

from config.config import db_config

def get_mysql_connection():

    try : 

        connection = mysql.connector.connect( **db_config )

        if connection.is_connected() :
            print('coneection OK!')
            return connection
    
    except Error as e:
        print('Error while connectiong to MySQL', e)
        return None
