"""database.py
contains database setup and connection infrastructure"""
import sqlalchemy as sa
from sqlalchemy import orm

rel = orm.relation
backref = orm.backref

setAttrs = lambda self, **kw: [setattr(self, k, v) for k,v in kw.items()]

def orMap(table, **kwargs):
    def decorator(cls, table=table, kwargs=kwargs):
        orm.mapper(cls, table, **kwargs)
        return cls
    return decorator


DBMeta = sa.MetaData()


class DB(object):

    engine = None
    begin = None

    def __init__(self, conf):
        if not self.engine:
            path = conf.db.postgres_path.format(**vars(conf.db))
            self.engine = sa.create_engine(path, echo=conf.debug)
            self.begin = orm.sessionmaker(bind=self.engine)

    def setupDB(self):
        DBMeta.create_all(self.engine)

