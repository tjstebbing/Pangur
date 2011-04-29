from werkzeug.exceptions import HTTPException
from werkzeug import redirect

class RedirectException(HTTPException):

    def __init__(self, location):
        self.location = location

    def __str__(self):
        return self.location

    def handler(self, request):
        # str() to avoid unicode, which suffers IRI encoding.
        request.response = redirect(str(self.location))
