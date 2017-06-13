from functools import wraps
from flask import request, Response


""" Adapted from:
" http://flask.pocoo.org/snippets/8/
"""

def check_auth(username, password):
    """ This function is called to check if a username /
    " password combination is valid.
    """
    from sshail import sshails

    user = sshails.user_data(username)
    return user and user.get('basic_passwd', None) == password


def authenticate():
    """ Sends a 401 response that enables basic auth """

    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials',
        401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )


def basic_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated
