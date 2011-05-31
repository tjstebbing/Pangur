from pangur import conf, init, registerTemplates

conf.setPaths(__file__)
conf.db.name = "listful.db"
conf.db.path = "sqlite:///{name}"

# setup static file serving for dev, in production these are served by nginx.
conf.dev.static_resources = {
    '/images' : '{root}/static/images',
    '/css' : '{root}/static/css',
    '/js' : '{root}/static/js',
}

#register the directory with our templates
registerTemplates(__file__, 'templates')

#create our WSGI application object
application = init(conf, __package__)
