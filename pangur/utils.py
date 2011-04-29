from os.path import join as opj, normpath as opn, dirname as opd
import re, urlparse, datetime

from werkzeug.routing import Map, Rule

url_map = Map()

class PermRule(Rule):

    def __init__(self, string, defaults=None, subdomain=None, methods=None,
                 build_only=False, endpoint=None, strict_slashes=None,
                 redirect_to=None, permission=None, template=None, func=None,
                 authRequired=False):
        Rule.__init__(self, string, defaults, subdomain, methods, build_only,
                      endpoint, strict_slashes, redirect_to)
        self.permission = permission
        self.template = template
        self.func = func
        self.authRequired = authRequired

    def match(self, path):
        values = Rule.match(self, path)
        if values is not None:
            values['authRequired'] = self.authRequired
            values['permission'] = self.permission
            values['template'] = self.template
            values['func'] = self.func
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


decoratorRegistries = {}
def createRegistryDecoratorWithArgs(registryName):
    """
    registerChook = createRegistryDecorator('chooks')

    @registerChook(breed='bantam')
    def brrrrrkkkkk():
        pass

    print decoratorRegistries['chooks']
    [(<function brrrrrkkkkk at 0x7f4e0b77c410>, (), {'breed': 'bantam'})]
    """
    decoratorRegistries[registryName] = []
    def decorator(*args, **kwargs):
        def decorate(item):
            decoratorRegistries[registryName].append((item, args, kwargs))
            return item
        return decorate
    return decorator

def createRegistryDecorator(registryName):
    """
    registerChook = createRegistryDecorator('chooks')

    @registerChook
    def brrrrrkkkkk():
        pass

    print decoratorRegistries['chooks']
    [(<function brrrrrkkkkk at 0x7f4e0b77c410>, (), {})]
    """
    decoratorRegistries[registryName] = []
    def decorate(item):
        decoratorRegistries[registryName].append((item, (), {}))
        return item
    return decorate


def relative(request, path="", hash="", **kwargs):
    """url helper, curry with the request to something like request.relative:

    given example.com/1/2 as the current URL:

    request.relative('../foo')                   example.com/1/foo
    request.relative('bar', foo=123)             example.com/1/2/bar?foo=123
    request.relative('bar', hash='b', foo=123)   example.com/1/2/bar?foo=123#b
    """
    path = opn(opj(request.path, path)).replace("\\","/")
    if kwargs:
        path = "%s?%s" % (path,
                          "&".join(['%s=%s' % (k,v) for k,v in kwargs.items()]))
    if hash:
        path = "%s#%s" % (path, hash)
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
            now = datetime.datetime.now()

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
