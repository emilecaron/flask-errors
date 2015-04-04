# -*- coding: utf8 -*-
'''
flask-error module
'''

from datetime import datetime
from functools import wraps
import sqlite3

class FlaskError:
    '''
        The FlaskError extension.

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
        return 'TONS OF ERRORS'



def _cursor(func):
    ''' Provide a cusor and commit to a method '''

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        cursor = self._conn.cursor()
        ret = func(self, cursor, *args, **kwargs)
        self._conn.commit()
        return ret

    return wrapper


class ErrorDb:
    '''
    Interface to the sqlite database
    Exposes methods for error storage
    '''
    _conn = None

    def __init__(self, db_file):
        self._conn = sqlite3.connect(db_file)
        self._seed()

    @_cursor
    def _seed(self, cursor):
        ''' Create required table if missing '''

        sqlcheck = "SELECT name FROM sqlite_master WHERE type='table' AND name='errors'"
        sqlcreate = 'CREATE TABLE errors(id integer primary key, \
                     type text, timestamp text, stacktrace text)'

        cursor.execute(sqlcheck)
        if not cursor.fetchall():
            cursor.execute(sqlcreate)

    @_cursor
    def store_error(self, cursor, error):
        sql_insert = 'INSERT INTO errors VALUES (?, ?, ?, ?)'

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


    @_cursor
    def get_errors_json(self, cursor, error):
        pass

