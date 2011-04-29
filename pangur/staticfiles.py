from os.path import join as opj, isfile, basename

import werkzeug
from werkzeug import exceptions


class FileServer(werkzeug.SharedDataMiddleware):
    """
    Serve up static files from multiple directories.

    Caches files, supports 304 Not Modified.
    """

    def __init__(self, paths):
        fallback = exceptions.NotFound()
        werkzeug.SharedDataMiddleware.__init__(self, fallback, {})
        self.exports['/'] = self.customLoader
        self.searchPath = paths

    def customLoader(self, path):
        """Search each static dir, take the first file found."""
        if path is not None:
            for base in self.searchPath:
                p = opj(base, path)
                if isfile(p):
                    return basename(p), self._opener(p)
        return None, None
