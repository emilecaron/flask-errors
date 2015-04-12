from flask import Flask
#from flask.ext.flask-errors import FlaskError
from errors import FlaskError

app = Flask(__name__)
FlaskError(app)

'''
    Example app
'''


class HomemadeError(Exception):
    pass


@app.errorhandler(Exception)
def exception(error):
    return "500 fuck you"


@app.errorhandler(HomemadeError)
def sweet_exception(error):
    return "500 have a nice day"


@app.route("/base")
def hello():
    raise Exception("Hello World!")


@app.route("/better")
def better():
    raise HomemadeError("Hello Better World!")


if __name__ == '__main__':
    app.run(debug=True)
