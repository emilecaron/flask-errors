# flask-errors
A simple flask extension for out of the box error management

# What it does
* Store any error in a local persistant sqlite database
* Provide a simple UI with error list and details
* Provide a rest endpoint to the errors data

# How to use
Two extra lines are required in your flask application:
```
from errors import FlaskError
FlaskError(app)
```
See full example in provided app.py file

# Default settings
* UI is available at /errors_ui
![flask-error](https://raw.github.com/emilecaron/flask-errors/master/screenshot.png)
* REST endpoint is available at /errors
* Errors are stored for 10 days

# Tech stack
None. This extension will run on a clean python3 + flask install.
The provided UI uses Bootstrap through the official CDNs.

# Next steps
Stats module
https://packaging.python.org/en/latest/distributing.html#initial-files

