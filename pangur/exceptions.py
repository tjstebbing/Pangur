from werkzeug.exceptions import HTTPException
from werkzeug import exceptions, redirect

NotFound = exceptions.NotFound

class RedirectException(HTTPException):
    """Raise this to perform a redirect"""

    def __init__(self, location):
        self.location = location

    def __str__(self):
        return self.location

    def handler(self, request):
        # str() to avoid unicode, which suffers IRI encoding.
        request.response = redirect(str(self.location))



