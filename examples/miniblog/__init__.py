from pangur import registerTemplates, conf, init

conf.setPaths(__file__)
conf.db.name = "miniblog"
conf.db.path = "sqlite:////tmp/{name}"
registerTemplates(__file__, 'templates')
application = init(conf, __package__)
