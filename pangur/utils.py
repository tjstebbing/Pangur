from os.path import join as opj, normpath as opn, dirname as opd
from types import FunctionType, ClassType
from collections import MutableMapping, namedtuple
from urlparse import urljoin
import re, datetime, inspect

import werkzeug
from werkzeug import urls
from werkzeug.routing import Map, Rule

from .globals import conf

quote = urls.url_quote_plus # percent escape, encode unicode.
unquote = urls.url_unquote_plus # un-escape and decode to unicode.
quote_path = urls.url_quote # preserve '/' and ':'
url_encode = urls.url_encode # dict -> query args.


def escape(s):
    """Replace html special characters & < > and quotes " ' """
    # NB. &apos; does not work in IE.
    return (s.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
             .replace('"',"&quot;").replace("'","&#39;"))


url_map = Map()

class PermRule(Rule):

    def __init__(self, string, defaults=None, subdomain=None, methods=None,
                 build_only=False, endpoint=None, strict_slashes=None,
                 redirect_to=None, permission=None, template=None, func=None,
                 authRequired=False, expires=None, mimetype=None):
        Rule.__init__(self, string, defaults, subdomain, methods, build_only,
                      endpoint, strict_slashes, redirect_to)
        self.permission = permission
        self.template = template
        self.func = func
        self.authRequired = authRequired
        self.expires = expires
        self.mimetype = mimetype

    def match(self, path):
        values = Rule.match(self, path)
        if values is not None:
            values['authRequired'] = self.authRequired
            values['permission'] = self.permission
            values['template'] = self.template
            values['func'] = self.func
            values['expires'] = self.expires
            values['mimetype'] = self.mimetype
        return values

def map(rule, template=None, **kw):
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
    url_map.add(_rule)
    def dataFuncDecorator(func, _rule=_rule):
        _rule.func = func
        return func
    return dataFuncDecorator

class FormsRegistry(object):

    forms = {}

    def __init__(self, request=None):
        self.request = request
        self.requestForms = {}

    def populateForm(self, form, source=None):
        if isinstance(source, dict):
            form.process(**source)
        elif source is not None:
            form.process(obj=source)
        return form

    def load(self, name, source=None):
        if name in self.requestForms:
            return self.populateForm(self.requestForms[name], source)
        if name in self.forms:
            if self.request.form.get(name):
                self.requestForms[name] = self.forms[name](self.request.form)
            else:
                self.requestForms[name] = self.forms[name]()
            return self.populateForm(self.requestForms[name], source)
        else:
            raise KeyError(name)

    def __call__(self, formClass):
        self.forms[formClass.__name__] = formClass
        return formClass

#decorate forms with me so they are available in templates
registerForm = FormsRegistry()

_slugify_strip_re = re.compile(r'[^\w\s-]')
_slugify_hyphenate_re = re.compile(r'[-\s]+')


def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.

    From Django's "django/template/defaultfilters.py".
    """
    import unicodedata
    if not isinstance(value, unicode):
        value = unicode(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(_slugify_strip_re.sub('', value).strip().lower())
    return _slugify_hyphenate_re.sub('-', value)


class RegistryDecorator(MutableMapping):
    """
    Create a decorator that builds a mapping of decorated functions/classes.

    You can access the registry contents as a Mapping, where the stored
    keys and values are determined by a custom inserter function.

    If no custom inserter is given, the behaviour depends on withArgs:
    when True, a namedtuple (item, args, kwargs) is inserted;
    when False, the function/class itself is inserted.

    Arguments::

        name:
            registry name for debugging and logging.

        inserter(registry, func, *args and **kwargs):
            Callable that validates arguments and inserts the decorated
            function/class (or any other value) into the registry.

        autoCall:
            if True (the default), the decorator can be used with or without
            calling it; direct use will be detected by checking for a single
            argument of function/class type. This will not work if the
            decorator needs to support a use-case where a single positional
            argument of function/class type will be passed; in that case use
            autoCall=False.

        withArgs:
            if True (the default), the decorator is allowed to take arguments,
            otherwise an assertion will be raised. When autoCall is False,
            this option determines whether the decorator must be called first
            or used directly.

        standAlone:
            if True (default is False), the decorator can also be used without
            decorating anything, to register its arguments only. In that case,
            the inserter must be supplied, and will be passed func=None.
    """

    RegistryItem = namedtuple('RegistryItem', ['func','args','kwargs'])

    def __init__(self, name, inserter=None, autoCall=True, withArgs=True,
                 standAlone=False, unique=True, debug=False, doc=None):
         self.name = name
         if doc: self.__doc__ = doc
         self.inserter = inserter
         self.autoCall = autoCall
         self.withArgs = withArgs
         self.standAlone = standAlone
         self.unique = unique
         self.debug = debug
         self.mapping = {}
         self.pending = None
         if standAlone:
            assert callable(inserter), "inserter must be provided when standAlone=True"

    def __str__(self):
        return "<%s.%s '%s' at 0x%08x>" % (self.__module__, self.__name__,
                                           self.name, id(self))

    def _finish(self):
        """Add a pending stand-alone decorator to the registry."""
        if self.pending is not None:
            args, kwargs = self.pending
            self.pending = None
            if self.inserter:
                self.inserter(self, None, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        """Use the registry as a decorator on a function class."""
        # handle pending stand-alone decorators.
        if self.pending is not None:
            self._finish()
        # detect use as a decorator without a call to the decorator by
        # checking if the first and only argument is a function or class.
        isDecorating = (len(args) == 1 and not kwargs and
                        isinstance(args[0], (FunctionType,ClassType)))
        func = None
        indirect = False
        if self.autoCall:
            if isDecorating:
                # used to decorate, without a call to pass args.
                func,args = args[0],args[1:]
            else:
                # called with args, return a decorate function.
                indirect = True
            if not self.withArgs:
                assert not (args or kwargs), "decorator is not allowed to "\
                                             "take arguments"
        else:
            # withArgs determines whether we expect a call to the decorator
            # with arguments before the decoration call.
            if self.withArgs:
                # called with args, return a decorate function.
                indirect = True
            else:
                # can only be used directly without an args call.
                assert isDecorating, "decorator is not allowed to "\
                                     "take arguments"
                func,args = args[0],args[1:]
        # make a callable that will register a decorated item.
        def _decorate(func):
            if self.inserter:
                self.inserter(self, func, *args, **kwargs)
            elif self.withArgs:
                self[func.__name__] = (func, args, kwargs)
            else:
                self[func.__name__] = func
            return func
        # register the decorated item now, unless indirect.
        if not indirect:
            return _decorate(func)
        # track unused decorators for error reporting.
        info = None
        if self.debug and indirect and not self.standAlone:
            info = inspect.getframeinfo(inspect.stack()[-1])
        if self.standAlone:
            self.pending = (args,kwargs)
        # return the decorate function to apply to the function/class.
        return _decorate

    # implement MutableMapping abstract base class.

    def __len__(self):
        if self.pending is not None:
            self._finish()
        return len(self.mapping)

    def __iter__(self):
        if self.pending is not None:
            self._finish()
        return iter(self.mapping)

    def __getitem__(self, key):
        if self.pending is not None:
            self._finish()
        return self.mapping[key]

    def __setitem__(self, key, value):
        if self.pending is not None:
            self._finish()
        if self.unique:
            assert key not in self.mapping, "registry key must be unique"
        self.mapping[key] = value
        if self.debug:
            print "[registry '%s': added %r -> %r]" % (self.name, key, value)

    def __delitem__(self, key):
        if self.pending is not None:
            self._finish()
        ret = dict.__delitem__(self.mapping, key)
        if self.debug:
            print "[registry '%s': removed %r]" % (self.name, key)
        return ret


def registryDecorator(_usedWithoutCall=None, **kwargs):
    """
    Declare a RegistryDecorator by decorating an insert function.

    Creates a RegistyDecorator using the decorated function as the inserter
    and the decorated function's name as the registry's debug name.

    See RegistryDecorator for other available keyword arguments.

    Examples:
        @pangur.registry
        def renderer(registry, func, foo=None, bar=True):
            registry[func.__name__] = Something(func, foo, bar)

        @pangur.registry(standAlone=True)
        def renderer(registry, func, ...):
            registry[func.__name__] = something
    """
    def _createRegistryDecorator(func):
        assert callable(func), "@registry must decorate a function"
        return RegistryDecorator(func.__name__, func,
                                 doc=func.__doc__, **kwargs)
    if _usedWithoutCall is not None:
        assert not kwargs, "@registry only accepts keyword arguments"
        return _createRegistryDecorator(_usedWithoutCall)
    return _createRegistryDecorator


def relative(request, path="", hash="", **kwargs):
    """url helper, curry with the request to something like request.relative:

    given example.com/1/2 as the current URL:

    request.relative('../foo')                   example.com/1/foo
    request.relative('bar', foo=123)             example.com/1/2/bar?foo=123
    request.relative('bar', hash='b', foo=123)   example.com/1/2/bar?foo=123#b
    """
    path = opn(opj(request.path, path)).replace("\\","/")
    path = quote_path(path) # percent escape, handle unicode.
    if kwargs:
        path = "%s?%s" % (path, url_encode(kwargs))
    if hash:
        path = "%s#%s" % (path, quote(hash))
    return path


templatePaths = []
def registerTemplates(_file_, templateDir='templates'):
    """
    Add a template directory to the template search path.

    In __init__.py:

        registerTemplates(__file__)
        registerTemplates(__file__, 'templates')
    """
    path = opn(opj(opd(_file_), templateDir))
    templatePaths.append(path)
    print "templates:", path


staticPaths = []
def registerStatic(_file_, staticDir='static'):
    """
    Add a directory of static files to the web server.

    In __init__.py:

        registerStatic(__file__)
        registerStatic(__file__, 'static')
    """
    path = opn(opj(opd(_file_), staticDir))
    staticPaths.append(path)
    print "static:", path


#Modified from django utils

def pluralize(singular, plural, count):
    if count == 1:
        return singular
    return plural

def timesince(d, now=None):
    """
    Takes two datetime objects and returns the time between d and now
    as a nicely formatted string, e.g. "10 minutes".  If d occurs after now,
    then "0 minutes" is returned.

    Units used are years, months, weeks, days, hours, and minutes.
    Seconds and microseconds are ignored.  Up to two adjacent units will be
    displayed.  For example, "2 weeks, 3 days" and "1 year, 3 months" are
    possible outputs, but "2 weeks, 3 hours" and "1 year, 5 days" are not.

    Adapted from http://blog.natbat.co.uk/archive/2003/Jun/14/time_since
    """
    chunks = (
      (60 * 60 * 24 * 365, lambda n: pluralize('year', 'years', n)),
      (60 * 60 * 24 * 30, lambda n: pluralize('month', 'months', n)),
      (60 * 60 * 24 * 7, lambda n : pluralize('week', 'weeks', n)),
      (60 * 60 * 24, lambda n : pluralize('day', 'days', n)),
      (60 * 60, lambda n: pluralize('hour', 'hours', n)),
      (60, lambda n: pluralize('minute', 'minutes', n))
    )
    # Convert datetime.date to datetime.datetime for comparison.
    if not isinstance(d, datetime.datetime):
        d = datetime.datetime(d.year, d.month, d.day)
    if now and not isinstance(now, datetime.datetime):
        now = datetime.datetime(now.year, now.month, now.day)

    if not now:
        if d.tzinfo:
            now = datetime.datetime.now(d)
        else:
            now = datetime.datetime.utcnow()

    # ignore microsecond part of 'd' since we removed it from 'now'
    delta = now - (d - datetime.timedelta(0, 0, d.microsecond))
    since = delta.days * 24 * 60 * 60 + delta.seconds
    if since <= 0:
        # d is in the future compared to now, stop processing.
        return u'0 ' + 'minutes'
    for i, (seconds, name) in enumerate(chunks):
        count = since // seconds
        if count != 0:
            break
    s = '%(number)d %(type)s' % {'number': count, 'type': name(count)}
    if i + 1 < len(chunks):
        # Now get the second item
        seconds2, name2 = chunks[i + 1]
        count2 = (since - (seconds * count)) // seconds2
        if count2 != 0:
            s += ' and %(number)d %(type)s' % {'number': count2, 'type': name2(count2)}
    return s


def populateFromForm(form, obj, fields):
    for name, field in form._fields.iteritems():
        if name in fields:
            field.populate_obj(obj, name)

def jinjaWidget(field, **kwargs):
    """This is a WTForms widget that passes everything to a jinja macro"""
    return kwargs['macro'](field)

def getIP(request):
    """Get client IP address X-Forwarded-For path."""
    # NB. this assumes you're always behind a proxy in production,
    # otherwise X-Forwarded-For can be fake.
    return request.headers.get('X-Forwarded-For') or request.remote_addr


def readFile(name, mode="rt"):
    """Read a file from the template directories."""
    dirs = conf.paths.templates + templatePaths
    for path in dirs:
        try:
            f = open(opj(path,name), mode)
            text = f.read()
            f.close()
            return text
        except IOError:
            continue
    raise IOError(2, "%s not found in %s" % (name, ', '.join(dirs)))
