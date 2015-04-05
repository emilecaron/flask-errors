from flask import Flask
#from flask.ext.flask-errors import FlaskError
from errors import FlaskError

app = Flask(__name__)
FlaskError(app)

'''
    Example app
'''


class Hello(Exception):
    pass

@app.route('/')
def hello_world():
    raise Hello('World')

if __name__ == '__main__':
    #app.run(debug=True)
    app.run(debug=False)
