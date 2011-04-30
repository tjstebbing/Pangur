from pangur import utils
from pangur.service import init
from pangur.globals import conf

conf.db.name = "miniblog"
conf.db.path = "sqlite:////tmp/{name}"

utils.registerTemplates(__file__, 'templates')

conf.setPaths(__file__)
init(conf, __package__)
