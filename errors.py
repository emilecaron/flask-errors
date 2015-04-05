# -*- coding: utf8 -*-
'''
flask-error module
a persistant storage for flask app errors
with easy access and no external dependency
'''

import sqlite3
import json
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

        self._db.store_error(error)

        # Propagate exception
        raise error

    def api(self):
        ''' handle queries to error route '''
        return self._db.get_errors_json()



def _cursor(func):
    '''
    Provide a cusor and commit to a method
    Requires the instance to have a db_file attribute
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
    '''
    db_file = None

    def __init__(self, db_file):
        self.db_file = db_file
        self._seed()

    @_cursor
    def _seed(self, cursor):
        ''' Create required table if missing '''

        sqlcheck = "SELECT name FROM sqlite_master WHERE type='table' AND name='errors'"
        sqlcreate = 'CREATE TABLE errors(id integer primary key, \
                     type text, timestamp text, stacktrace text)' # ADD TEXT TEXT ><

        cursor.execute(sqlcheck)
        if not cursor.fetchall():
            cursor.execute(sqlcreate)

    @_cursor
    def store_error(self, cursor, error):
        sql_insert = 'INSERT INTO errors VALUES (NULL, ?, ?, ?)'

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(sql_insert, (error.__class__.__name__, timestamp, str(error)))

    @_cursor
    def get_errors_json(self, cursor):
        sqlget = ''' SELECT * FROM errors '''
        cursor.execute(sqlget)
        return json.dumps([str(x) for x in cursor.fetchall()])


