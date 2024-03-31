from flask_mysqldb import MySQL

def configure_database(app):
    mysql = MySQL(app)
    return mysql
