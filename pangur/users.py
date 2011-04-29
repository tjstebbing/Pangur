import sqlalchemy as sa

from pangur.database import orMap, DBMeta


userTable = sa.Table('users', DBMeta,
                     sa.Column('id', sa.Integer, primary_key=True),
                     sa.Column('username', sa.String, unique=True),
                     sa.Column('password', sa.String),
                     sa.Column('enabled', sa.Boolean, default=True),
                     sa.Column('admin', sa.Boolean, default=False))

@orMap(userTable)
class User(object):

    def __init__(self, username, password):
        self.username = username
        self.password = password



