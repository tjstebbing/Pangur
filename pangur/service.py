from werkzeug import Request, Response
from werkzeug.exceptions import NotFound
from jinja2 import Environment, PrefixLoader, FileSystemLoader

from pangur import session, utils, database, plugin, staticfiles
from pangur.exceptions import HTTPException, RedirectException
from pangur.utils import map, FormsRegistry

#grevious bodily hack, because jinja cant access __names  c_c
import wtforms
wtforms.Form.getFormName = lambda self: self.__class__.__name__

templates = None
db_conn = None
conf = None
static = None

#decorator to register before render funcs
beforeTemplateRender = utils.createRegistryDecorator('beforeTemplateRender')


def init(config, _package_=None):
    """Init application: pass config and __package__ to load."""
    global templates, db_conn, conf, static
    conf = config
    db_conn = database.DB(conf) #Establish a connection to the db
    #load all modules in the app package.
    if _package_:
        plugin.importPackage(_package_)
    #make jinja template environment.
    template_paths = conf.paths.templates + utils.templatePaths
    templates = Environment(loader=FileSystemLoader(template_paths))
    #print '\n'.join(templates.list_templates(filter_func=lambda n: not n.startswith('.')))
    #map static files.
    static = staticfiles.FileServer(utils.staticPaths)


def prepareToRender(request):
    request.forms = FormsRegistry(request)
    vars = {'request' : request, 'forms' : request.forms }
    for match in utils.decoratorRegistries['beforeTemplateRender']:
        match[0](request, vars)
    return vars

@Request.application
def application(request):
    adapter = utils.url_map.bind_to_environ(request.environ)
    try:
        endpoint, values = adapter.match()
        templateName = values['template']
        request.matches = values
        func = values['func']
        permission = values['permission']
        request.response = Response(mimetype='text/html')
        request.conf = conf
        request.db = db_conn
        request.txn = request.db.begin()
        request.session = session.Session(request)
        request.relative = lambda p="", **kw: utils.relative(request, p, **kw)
        templateVars = prepareToRender(request)
        #handle authRequired resource when user is not logged in
        if values['authRequired'] and not request.session.authenticated:
            raise RedirectException('/login?from='+request.path)
        if (not permission
            or getattr(request.session.user, permission, None)):
            #we are allowed to be here so..
            if templateName and callable(func):
                #call function and merge returned dict with templateVars
                #then render the template
                templateVars.update(func(request))
                template = templates.get_template(templateName)
                request.response.data = template.render(**templateVars)
            elif templateName:
                #just render the template vanilla, yum!
                template = templates.get_template(templateName)
                request.response.data = template.render(**templateVars)
            elif callable(func):
                #just call the function to handle the request
                data = func(request)
                if data is not None:
                    request.response.data = data
        elif request.session.authenticated:
            #we are logged in but should not be here, oops!
            template = templates.get_template("oops.html")
            request.response.data = template.render(**templateVars)
        else:
            #you are not logged in, eek, return to home, do not pass go
            #do not collect $200-
            raise RedirectException('/login?from='+request.path)

    except NotFound, e:
        # let the static file server respond or 404.
        return static
    except HTTPException, e:
        if hasattr(e, 'handler'):
            try:
                e.handler(request)
            except Exception, e:
                print "Exception Handling Error", e
        else:
            return e
    request.txn.commit()
    return request.response
