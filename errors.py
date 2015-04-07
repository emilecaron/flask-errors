# -*- coding: utf8 -*-

'''
flask-error module
a persistant storage for flask app errors
with easy access and no external dependency
'''

import sys
import os
import io
import json
import sqlite3
import traceback
from datetime import datetime, timedelta
from functools import wraps

from flask import request, abort, render_template_string


module_dir = os.path.dirname(__file__)

class FlaskError:
    '''
        The FlaskError class

        Use it this way:
            app = Flask(__name__)
            FlaskError(app)

    '''

    def __init__(self, app=None, db_file=None, expire=timedelta(days=10), **kwargs):
        '''
            Initialize FlaskError

            app: the Flask app instance
            db_file: the file to use as an sqlite database, or :memory:
            expire: timedelta, exceptions past this date will be removed
            errors_route: optional url to enable FlaskError api route 
            ui_route: optional url to enable FaskError ui route
        '''

        db_file = db_file or  app.root_path + '/errors.db'
        self._db = ErrorDb(db_file)
        self.expire = expire

        if app is not None:
            self.init_app(app, **kwargs)

    def init_app(self, app, errors_route='/errors', ui_route='/errors_ui'):
        # Propagate exceptions
        app.config['PROPAGATE_EXCEPTIONS'] = True

        # Register base handler
        app.errorhandler(BaseException)(self.handler)

        # Register api route
        if errors_route is not None:
            app.route(errors_route, methods=['GET'])(self.api)

        # Register UI route
        if ui_route is not None:
            app.route(ui_route, methods=['GET'])(self.ui_root)
            app.route(ui_route + '/error/<int:error_id>', methods=['GET'])(self.ui_error)

    def handler(self, error):
        ''' Handle any exception and propagate '''
        self._db.store_error(*sys.exc_info())
        self._db.expire(datetime.now() - self.expire)
        raise error

    def api(self):
        '''
        handle queries to error route
        returns the list of errors in the database as json data
        '''
        limit = request.args.get('limit', 10)
        return json.dumps(self._db.get_errors(limit))

    def ui_root(self):
        '''
        handles queries to ui default route
        renders root template
        '''
        with open(module_dir + '/root.html', 'r') as tpl_file:
            tpl = tpl_file.read()
            errors = self._db.get_errors(100)
            return render_template_string(tpl, errors=errors)

    def ui_error(self, error_id):
        '''
        handles queries to specific error route
        renders error template
        '''
        error = self._db.get_error(error_id)
        if not error:
            abort(404)
        with open(module_dir + '/error.html', 'r') as tpl_file:
            tpl = tpl_file.read()
            return render_template_string(tpl, error=error)


def _cursor(func):
    '''
    Provide a cusor and autocommit to a method
    Requires the class/instance to have a db_file attribute
    '''

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        conn = sqlite3.connect(self.db_file, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = conn.cursor()
        try:
            ret = func(self, cursor, *args, **kwargs)
            conn.commit()
            return ret
        except sqlite3.Error:
            conn.rollback()
            raise
        finally:
            conn.close()
    return wrapper


class ErrorDb:
    '''
    Interface to the sqlite database
    Exposes methods for error storage

    An exception is stored using the following schema:
      id, timestamp, type, value, traceback

    The json output will be the same
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
        values = (datetime.now(), exc_type.__name__, str(exc_value), traceback_io.getvalue())
        sql_insert = 'INSERT INTO errors VALUES (NULL, ?, ?, ?, ?)'
        cursor.execute(sql_insert, values)

    @_cursor
    def get_errors(self, cursor, limit=10):
        ''' Get the data associated with the error'''
        sqlget = 'SELECT * FROM errors ORDER BY timestamp DESC LIMIT ? '
        cursor.execute(sqlget, (limit,))
        return [self._build_json(e) for e in cursor.fetchall()]

    @_cursor
    def get_error(self, cursor, error_id):
        ''' Get the data associated with a specific error'''
        sqlget = 'SELECT * FROM errors WHERE id=? '
        cursor.execute(sqlget, (error_id,))
        data = cursor.fetchone()
        return self._build_json(data) if data else None

    def _build_json(self, row):
        ''' return a json obj from a row result '''
        key, timestamp, exc_type, value, traceback = row
        return {
            'id': key,
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'type': exc_type,
            'value': value,
            'traceback': traceback,
        }

    @_cursor
    def expire(self, cursor, expire_date):
        ''' Remove expired errors '''
        sqldel = 'DELETE FROM errors WHERE timestamp < ? '
        cursor.execute(sqldel, (expire_date,))

