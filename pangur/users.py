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

    def hasPermission(self, permission):
        """
        Check if this user has a permission specified by dot path.

        Examples:
            user.hasPermission("admin")
            user.hasPermission("account.active")

        In this example, the user's Account ORM class has installed a backref
        named 'account' on User objects, and this permission check traverses
        the relationship.
        """
        obj = self
        for perm in permission.split('.'):
            obj = getattr(obj, perm, None)
        return bool(obj)

