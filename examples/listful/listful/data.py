from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm.session import object_session
from pangur import (DBMeta, orMap, rel, backref, User)

#holds our tasks
taskTable = sa.Table('tasks', DBMeta,
                        sa.Column('id', sa.Integer, primary_key=True),
                        sa.Column('text', sa.String),
                        sa.Column('createdOn', sa.DateTime),
                        sa.Column('createdBy', sa.Integer,
                                  sa.ForeignKey('users.id')),
                        sa.Column('completedOn', sa.DateTime),
                        sa.Column('completedBy', sa.Integer,
                                  sa.ForeignKey('users.id')))
#holds our lists
listTable = sa.Table('lists', DBMeta,
                        sa.Column('id', sa.Integer, primary_key=True),
                        sa.Column('name', sa.String))

#holds task logs
logTable = sa.Table('logs', DBMeta,
                        sa.Column('id', sa.Integer, primary_key=True),
                        sa.Column('taskId', sa.Integer,
                                  sa.ForeignKey('tasks.id')),
                        sa.Column('text', sa.String),
                        sa.Column('when', sa.DateTime),
                        sa.Column('userId', sa.Integer,
                                  sa.ForeignKey('users.id')))

#relates tasks to lists
taskListsTable = sa.Table('task_lists', DBMeta,
                        sa.Column('taskId', sa.Integer,
                                  sa.ForeignKey('tasks.id')),
                        sa.Column('listId', sa.Integer,
                                  sa.ForeignKey('lists.id')))

#relates lists to users
listUsersTable = sa.Table('list_users', DBMeta,
                        sa.Column('userId', sa.Integer, sa.ForeignKey('users.id')),
                        sa.Column('listId', sa.Integer, sa.ForeignKey('lists.id')))


@orMap(listTable, properties={'users' : rel(User, secondary=listUsersTable,
                                            backref=backref('lists'))})
class List(object):

    def __init__(self, name):
        self.name = name

    def addTask(self, task):
        self.tasks.append(task)

    def removeTask(self, task):
        self.tasks.remove(task)


@orMap(taskTable, properties={
    'creator' : rel(User, primaryjoin=User.id==taskTable.c.createdBy,
                    backref='createdByMe'),
    'completor' : rel(User, primaryjoin=User.id==taskTable.c.completedBy,
                      backref='completedByMe'),
    'lists' : rel(List, secondary=taskListsTable, backref='tasks') })
class Task(object):

    def __init__(self, text, creator):
        self.text = text
        self.creator = creator
        self.createdOn = datetime.now()

    def complete(self, completor):
        self.completor = completor
        self.completedOn = datetime.now()

    def uncomplete(self):
        self.completor = None

    def log(self, text, who=None):
        txn = object_session(self)
        txn.add(Log(self, text, who))


@orMap(logTable, properties={'task' : rel(Task, backref='logs'),
                             'who' : rel(User)})
class Log(object):

    def __init__(self, task, text, who):
        self.task = task
        self.text = text
        self.who = who
        self.when = datetime.now()
