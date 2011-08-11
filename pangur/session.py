"""
Session management and authentication

the request object passed to your @map'd functions has a Session instance on
it which will take care of session cookies; 'request.session'. If the session
is authenticated (request.session.authenticated), then 'request.session.user'
will contain the currently logged in user, otherwise None.

If you're doing a standard username/password site then we have some helpers
to make this a simple task:

createUser(request, username, password):  will return a newly created user
with those credentials and ensure that the password is sufficiently hashed
so that it can be safely stored in the database.

validateCredentials(request, username, password): will hash the provided
password and check if it matches an existing user, returns a boolean.

To login a user you just need to raise LoginException with the name of the
user you would like to login, to logout simply raise LogoutException, both
take a 'location' parameter which will determine where to redirect the user
after loging in or out.

In summary, you can use the createUser and validateCredentials helpers to
easily manage creating and authenticating users, and then action login/logout
requests with the above eceptions. If you need to implement a more complicated
or different system you can implement that using our exceptions as well after
you have authenticated in yur own way.
"""

from datetime import datetime, timedelta
import hmac

from werkzeug.utils import redirect

from .users import User
from .passwd import checkPassword, hashPassword
from .exceptions import HTTPException

_s = "The Quick Spotty Skunk Jumped Over The Lazy Horned Owl"
secret = lambda n,o=-0:(n+timedelta(hours=o)).strftime("%Y%m%d%H")
hash = lambda s, now, offset=-0: hmac.new(secret(now,offset), s).hexdigest()
compare = lambda s, h, now, offset=-0: hash(s, now, offset) == h

class Session(object):

    def __init__(self, request):
        self.request = request
        self._user = None
        self.username = None
        self.authenticated = False
        self.cookieAuth() #always try cookie auth

    @property
    def user(self):
        if not self.authenticated:
            return None
        if not self._user:
            txn = self.request.txn
            self._user = txn.query(User).filter(
                User.username == self.username).first()
        return self._user

    def hasPermission(self, permission):
        """Check if the user has a permission; False if no user."""
        user = self.user
        if user:
            return user.hasPermission(permission)
        return False

    def auth(self, username):
        self.username = username
        self.authenticated = True

    def cookieAuth(self):
        self.username = self.request.cookies.get('nom')
        self.crumpet = self.request.cookies.get('crumpet')
        if self.username and hash:
            now = datetime.utcnow()
            if compare(self.username, self.crumpet, now):
                self.authenticated = True
            elif compare(self.username, self.crumpet, now, -1):
                self.authenticated = True
                self.newCredentials(self.username)
            else:
                self.blankCredentials()

    def newCredentials(self, username):
        self.request.response.set_cookie('nom', username)
        self.request.response.set_cookie('crumpet', hash(username,
                                                         datetime.utcnow()))
    def blankCredentials(self):
        self.request.response.delete_cookie('nom')
        self.request.response.delete_cookie('crumpet')


class LoginException(HTTPException):
    """Raise this when a user successfully authenticates"""

    def __init__(self, username, location):
        self.username = username.lower()
        self.location = location

    def __str__(self):
        return self.location

    def handler(self, request):
        request.response = redirect(self.location)
        request.session.newCredentials(self.username)


class LogoutException(HTTPException):
    """Raise this to logout a user"""

    def __init__(self, location):
        self.location = location

    def __str__(self):
        return self.location

    def handler(self, request):
        request.response = redirect(self.location)
        request.session.blankCredentials()


def createUser(request, username, password):
    """Create a basic user, hashing their password"""
    username = username.lower()
    if request.txn.query(User).filter_by(username=username).first():
        return False
    user = User(username, hashPassword(password))
    request.txn.add(user)
    return user

def validateCredentials(request, username, password):
    username = username.lower()
    usr = request.txn.query(User).filter_by(username=username,
                                            enabled=True).first()
    if usr:
        return checkPassword(password, usr.password)
    return False
