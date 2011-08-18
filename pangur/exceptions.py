from werkzeug.exceptions import HTTPException
from werkzeug import exceptions, redirect

NotFound = exceptions.NotFound

class RedirectException(HTTPException):
    """Raise this to perform a redirect"""

    def __init__(self, location):
        # str() to avoid unicode, which suffers IRI encoding.
        self.location = str(location)

    def __str__(self):
        return self.location

    def handler(self, request):
        request.response = redirect(self.location)



