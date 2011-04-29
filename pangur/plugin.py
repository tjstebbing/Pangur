import os

from werkzeug import routing
from sqlalchemy import orm
import sqlalchemy as sa

from . import utils, database
from .utils import PermRule, FormsRegistry


# ---- plugin module/package  loading

def loadPlugins(pluginDir):
    """Load all plugins inside a plugin directory."""
    print "plugins:", pluginDir
    raise 1
    import sys
    sys.path.insert(0, pluginDir)
    plugins = []
    for ent in os.listdir(pluginDir):
        dir = os.path.join(pluginDir, ent)
        if os.path.isfile(os.path.join(dir, '__init__.py')):
            plugins.append(ent)
            _walkPackage(dir, ent)
    return plugins

def importPackage(_name_):
    """Load all modules and packages within the named package."""
    print "import:", _name_
    if '.' in _name_:
        path = _name_.split('.')
        pkgname,fromlist = '.'.join(path[0:-1]), [path[-1]]
    else:
        pkgname,fromlist = _name_, []
    pkg = __import__(pkgname, globals(), {}, fromlist, 0)
    dir = os.path.dirname(pkg.__file__)
    _walkPackage(dir, pkg.__name__)

def _walkPackage(dir, name):
    """Import all modules and packages within a package."""
    print "... package", name, dir
    __import__(name, globals(), {}, [], 0)
    for ent in os.listdir(dir):
        if ent.endswith(".py") and ent != '__init__.py':
            mod = "%s.%s" % (name, ent[:-3])
            print "... module", mod
            __import__(mod, globals(), {}, [], 0)
        elif ent != 'test':
            pkg = os.path.join(dir, ent)
            if os.path.isfile(os.path.join(pkg, '__init__.py')):
                _walkPackage(pkg, "%s.%s" % (name, ent))


# ---- pangur plugins

def makeMap():
    """Make an @map decorator for a plugin."""
    return utils.map # just the global map for now!

def makeOrMap():
    """Make an @orMap decorator for a plugin."""
    return database.orMap # just the global orMap for now.

def makeDBMeta():
    """Make database metadata registry for a plugin."""
    return database.DBMeta # just the global DBMeta for now.

def makeRegisterForm():
    """Make an @registerForm decorator for a plugin."""
    return utils.registerForm # just the global registry for now!


class ClassInstance(object):
    """Lazily calls a factory to set a class attribute."""
    def __init__(self, name, factory):
        self.name, self.factory = name, factory
    def __get__(self, instance, owner):
        assert instance is None, 'should not reach here'
        obj = owner.__dict__.get(self.name)
        if obj is None:
            obj = self.factory()
            print "created", self.name, "for", owner
            type(owner).__setattr__(owner, self.name, obj)
        return obj


class Plugin(object):
    """
    Provides decorators for registering plugin contents.

    class MyPlugin(Plugin):
        ...

    @MyPlugin.map('/foo', 'foo.html')
    def foo(request):
        return {'bar' : 123}
    """

    url_map = ClassInstance('url_map', routing.Map)
    registerForm = ClassInstance('registerForm', FormsRegistry)
    DBMeta = ClassInstance('DBMeta', sa.MetaData)

    @classmethod
    def orMap(cls, table, **kwargs):
        def decorator(orcls, table=table, kwargs=kwargs):
            orm.mapper(orcls, table, **kwargs)
            return cls
        return decorator

    @classmethod
    def map(cls, rule, template=None, **kw):
        """map is the decorator/function for mapping URLs to templates or
        functions, or both.

        EXAMPLES:

        #accessing /foo renders the foo.html template
        map('/foo', 'foo.html')

        #same as above but only for logged in users
        map('/foo', 'foo.html', authRequired=True)

        #same as above but only for admin
        map('/foo', 'foo.html', permission='admin')

        #call the foo function to handle the request manually
        @map('/foo')
        def foo(request):
            ...

        #call the foo function to return a dict which is passed into the template
        @map('/foo', 'foo.html')
        def foo(request):
            return {'bar' : 123}
        """
        kw['template'] = template
        kw['endpoint'] = 'no endpoint'
        _rule = PermRule(rule, **kw)
        cls.url_map.add(_rule)
        def dataFuncDecorator(func):
            _rule.func = func
            return func
        return dataFuncDecorator
