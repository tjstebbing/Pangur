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
so that it can be safely stored in the database. Usernames can be any unicode
text, which we normalize (see normalizeUsername) for comparing and storing.

validateCredentials(request, username, password): will hash the provided
password and check if it matches an existing user, returns the User.

normalizeUsername(username): returns the normalized form of the username
for comparison and storage. Strips leading and trailing whitespace, lower-
cases the name and converts to Unicode NFKD form.

To log in a user you just need to raise LoginException with the User.id of the
user you would like to log in. To log out, simply raise LogoutException. Both
take a 'location' parameter which will determine where to redirect the user
after logging in or out.

In summary, you can use the createUser and validateCredentials helpers to
easily manage creating and authenticating users, and then action login/logout
requests with the above eceptions. If you need to implement a more complicated
or different system, you can implement that using our exceptions as well after
you have authenticated in your own way.
"""

from datetime import datetime, timedelta
import hmac, unicodedata

from werkzeug.utils import redirect

from .users import User
from .passwd import checkPassword
from .exceptions import HTTPException
from .globals import conf
from .utils import getIP


secret = lambda n,o=-0: (conf.session.secret +
                            (n+timedelta(hours=o)).strftime("%Y%m%d%H"))
hash = lambda s, now, offset=-0: hmac.new(secret(now,offset),s).hexdigest()
compare = lambda s, h, now, offset=-0: hash(s, now, offset) == h


class Session(object):

    def __init__(self, request):
        assert conf.session.secret, "must configure a session secret"
        self.request = request
        self._user = None
        self.userId = None
        self.authenticated = False
        self.cookieAuth() #always try cookie auth

    @property
    def user(self):
        if not self.authenticated:
            return None
        if not self._user:
            self._user = self.request.txn.query(User).get(self.userId)
        return self._user

    @property
    def username(self):
        return self.user.username

    def hasPermission(self, permission):
        """Check if the user has a permission; False if no user."""
        user = self.user
        if user:
            return user.hasPermission(permission)
        return False

    def auth(self, userId):
        if userId != self.userId:
            self._user = None # userId changed.
        self.userId = userId
        self.authenticated = True

    def cookieAuth(self):
        crumpet = self.request.cookies.get('crumpet')
        if crumpet:
            # hexidecimal string, split by 'i' for some reason.
            # must be cookie-safe ascii characters.
            try:
                hexid,frob = crumpet.split('i')
                # bind session cookie to IP address for extra security.
                token = "%s:%s" % (hexid, getIP(self.request))
                now = datetime.utcnow()
                if compare(token, frob, now):
                    self.auth(int(hexid,16))
                elif compare(token, frob, now, -1):
                    self.newCredentials(int(hexid,16))
                    # unfortunately a new Session calls cookieAuth before
                    # it has been attached to its request.
                    self.request.session = self # for callbacks.
                    for func in conf.session.on_refresh:
                        func(self.request)
                else:
                    self.blankCredentials()
            except Exception as e:
                # malformed cookie.
                print "malformed session:", crumpet, str(e)
                self.blankCredentials()

    def newCredentials(self, userId):
        """Generate a new session cookie and make the session logged in."""
        self.auth(userId)
        hexid = hex(userId)[2:] # strip leading "0x"
        # bind session cookie to IP address for extra security.
        token = "%s:%s" % (hexid, getIP(self.request))
        crumpet = "%si%s" % (hexid, hash(token,datetime.utcnow()))
        self.request.response.set_cookie('crumpet', crumpet)

    def blankCredentials(self):
        self.request.response.delete_cookie('crumpet')


class LoginException(HTTPException):
    """Raise this when a user successfully authenticates"""

    def __init__(self, userId, location):
        self.userId = userId
        self.location = location

    def __str__(self):
        return self.location

    def handler(self, request):
        request.response = redirect(self.location)
        request.session.newCredentials(self.userId)
        for func in conf.session.on_login:
            func(request)


class LogoutException(HTTPException):
    """Raise this to logout a user"""

    def __init__(self, location):
        self.location = location

    def __str__(self):
        return self.location

    def handler(self, request):
        for func in conf.session.on_logout:
            func(request)
        request.response = redirect(self.location)
        request.session.blankCredentials()


def createUser(request, username, password):
    """Create a basic user, hashing their password"""
    username = normalizeUsername(username)
    # NB. this guard doesn't prevent a conflict when the transaction
    # commits - you might get a "concurrent modification" error if
    # someone else commits a createUser for the same username first.
    if request.txn.query(User).filter_by(username=username).first():
        return False
    user = User(username, password)
    request.txn.add(user)
    return user

def validateCredentials(request, username, password):
    """Check if credentials match a User in the database."""
    username = normalizeUsername(username)
    password = password.strip()
    usr = request.txn.query(User).filter_by(username=username,
                                            enabled=True).first()
    if usr and checkPassword(password, usr.password):
        return usr
    return None

def userExists(request, username):
    """Check if a username exists in the database."""
    username = normalizeUsername(username)
    usr = request.txn.query(User).filter_by(username=username).first()
    return (usr is not None)

def normalizeUsername(username):
    """Convert a username to canonical form for comparison."""
    result = username.strip().lower()
    if isinstance(result, unicode):
        return unicodedata.normalize('NFKD', result)
    return result
