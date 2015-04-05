# -*- coding: utf8 -*-

'''
flask-error module
a persistant storage for flask app errors
with easy access and no external dependency
'''

import sys
import io
import json
import sqlite3
import traceback
from datetime import datetime
from functools import wraps


class FlaskError:
    '''
        The FlaskError class

        Use it this way:
            app = Flask(__name__)
            FlaskError(app)

    '''

    def __init__(self, app=None, db_file='errors.db', **kwargs):
        '''
            Initialize FlaskError

            app: the Flask app instance
            db_file: the file to use as an sqlite database, or :memory:
            errors_route: optional url enable FlaskError api route 
        '''

        if app is not None:
            self.init_app(app, **kwargs)

        self._db = ErrorDb(db_file)


    def init_app(self, app, errors_route='/errors'):

        # Register base handler
        app.errorhandler(BaseException)(self.handler)

        # Register api route
        if errors_route is not None:
            app.route(errors_route, methods=['GET'])(self.api)

    def handler(self, error):
        ''' Handle any exception '''
        print('Handling', error, type(error))

        self._db.store_error(*sys.exc_info())

        # Propagate exception
        raise error

    def api(self):
        ''' handle queries to error route '''
        return self._db.get_errors_json()



def _cursor(func):
    '''
    Provide a cusor and commit to a method
    Requires the class/instance to have a db_file attribute
    '''

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        ret = func(self, cursor, *args, **kwargs)
        conn.commit()
        conn.close()
        return ret

    return wrapper


class ErrorDb:
    '''
    Interface to the sqlite database
    Exposes methods for error storage

    An exception is stored using the following schema:
      id, timestamp, type, value, traceback

    '''
    db_file = None

    def __init__(self, db_file):
        self.db_file = db_file
        self._seed()

    @_cursor
    def _seed(self, cursor):
        ''' Create required table if missing '''

        sqlcheck = "SELECT name FROM sqlite_master WHERE type='table' AND name='errors'"
        sqlcreate = 'CREATE TABLE errors(id integer primary key, timestamp timestamp, \
                                         type text, value text, traceback text)'

        cursor.execute(sqlcheck)
        if not cursor.fetchall():
            cursor.execute(sqlcreate)

    @_cursor
    def store_error(self, cursor, exc_type, exc_value, exc_traceback):
        ''' Extract data from error and store it'''
        traceback_io = io.StringIO()
        traceback.print_tb(exc_traceback, file=traceback_io)
        values = (datetime.now(), str(exc_type), str(exc_value), traceback_io.getvalue())
        sql_insert = 'INSERT INTO errors VALUES (NULL, ?, ?, ?, ?)'
        cursor.execute(sql_insert, values)

    @_cursor
    def get_errors_json(self, cursor):
        ''' Get the json data associated with the error'''
        sqlget = 'SELECT * FROM errors'
        cursor.execute(sqlget)
        return json.dumps([e for e in cursor.fetchall()])


