from datetime import datetime, timedelta
import hmac

from pangur.users import User


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
            self._user = txn.query(User).filter(User.username == self.username).first()
        return self._user

    def auth(self, username):
        self.username = username
        self.authenticated = True

    def cookieAuth(self):
        self.username = self.request.cookies.get('nom')
        self.crumpet = self.request.cookies.get('crumpet')
        if self.username and hash:
            now = datetime.now()
            if compare(self.username, self.crumpet, now):
                self.authenticated = True
            elif compare(self.username, self.crumpet, now, -1):
                self.authenticated = True
                self.newCredentials(self.username)
            else:
                self.blankCredentials()

    def newCredentials(self, username):
        self.request.response.set_cookie('nom', username)
        self.request.response.set_cookie('crumpet', hash(username, datetime.now()))

    def blankCredentials(self):
        self.request.response.delete_cookie('nom')
        self.request.response.delete_cookie('crumpet')

