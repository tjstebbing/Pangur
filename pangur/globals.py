from os import path

class Config(object):

    def setPaths(self, _file_):
        conf.paths.root = path.abspath(path.join(path.dirname(_file_), '..'))
        conf.paths.templates = [path.join(conf.paths.root,'templates')]

conf = Config()
conf.paths = Config()
conf.paths.root = '.'
conf.paths.templates = []
conf.db = Config()
conf.URLS = Config()
conf.dev = Config()

conf.debug = False
conf.URLS.login = "/login?from={fromPath}"
conf.URLS.no_permissions = "/oops"
conf.db.name = ""
conf.db.user = ""
conf.db.pwd = ""
conf.db.host = "localhost"
conf.db.port = 5432
conf.db.path = "postgresql://{user}:{pwd}@{host}:{port}/{name}"
conf.dev.port = 8000
conf.dev.interface = "127.0.0.1"
conf.dev.static_resources = {}
conf.secret = "" # must provide your own session secret.
