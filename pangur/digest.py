import hashlib, time, random
from pangur.exceptions import HTTPException
from pangur.users import User

_hash = lambda a: hashlib.md5(':'.join([str(b) for b in a])).hexdigest()
def hash(a):
    print a
    h = _hash(a)
    return h


def digestAuthenticate(f):
    def _(request, f=f):
        """decorator for requiring digest auth."""
        #ANSWER ME THESE QUESTIONS THREE, ERE THE OTHER SIDE YE SEE
        if not request.authorization:
            raise DigestAuthenticationException()
        auth = request.authorization
        #ask me the questions bridge keeper, I am not afraid!
        user = request.txn.query(User).filter(User.name == auth.username).first()
        password = user.password
        #WHAT IS YOUR NAME?
        HA1 = hash((auth.username, auth.realm, password))
        #WHAT IS YOUR QUEST?
        HA2 = hash((request.method, auth.uri))
        #WHAT IS YOUR FAVORITE COLOUR?
        HA3 = hash((HA1, auth.nonce, auth.nc, auth.cnonce, ','.join(auth.qop), HA2))
        print HA3
        print auth.response
        if HA3 != auth.response:
            #aaaaaaaaaaaaaaaaaahhhhhhhhhhhhhhhhhhhh
            raise DigestAuthenticationException()
        #orrite then, off you go
        request.session.auth(auth.username)
        f(request)
    return _

class DigestAuthenticationException(HTTPException):

    def __init__(self, realm="realm", stale=False):
        self.realm = realm
        self.stale = stale

    def handler(self, request):
        nonce = hash('%s:%s' % (time.time(), random.random()))
        request.response.www_authenticate.set_digest(self.realm, nonce)
        request.response.www_authenticate.stale = self.stale
        request.response.status_code = 401




