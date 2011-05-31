import json
from collections import namedtuple

from pangur import map

from .data import List, Task


def parseData(request, **args):
    X = namedtuple('X', args.keys())
    y = X(*args.values())
    try:
        return y._replace(**json.dumps(request.form['data']))
    except Exception, e:
        return y

class ListfulEncoder(json.JSONEncoder):

    def default(self, o):
        cls = type(o)
        if cls is List:
            return {'id' : o.id, 'name' : o.name}
        elif cls is Task:
            return {'id' : o.id, 'text' : o.text}
        return json.JSONEncoder.default(self, o)

encoder = ListfulEncoder()

@map('/api/list', authRequired=True)
def listLists(request):
    return encoder.encode(request.txn.query(List).all())


@map('/api/list/update', authRequired=True)
def updateList(request):
#    try:
    data = parseData(request, id=None, name="Innominate List")
    if data.id:
        l = request.txn.query(List).filter(List.id==data.id).first()
        l.name = data.name
    else:
        request.txn.add(List(data.name))
#    except Exception, e:
#
#        return json.dumps(False)
    return json.dumps(True)


@map('/api/task/update', authRequired=True)
def updateTask(request):
    try:
        data = parseData(request, id=None, text=None, completed=None)
        if data.id:
            t = request.txn.query(Task).filter(Task.id==data.id).first()
        else:
            t = Task(request.session.user, data.text)
            request.txn.add(t)
            t.log("created task", request.session.user)
        if data.completed is False:
            t.completed = False
            t.log("marked task as incomplete", request.session.user)
        elif data.completed is True:
            t.completed = True
            t.completedBy = request.session.user
            t.log("marked task as complete", request.session.user)
    except Exception, e:
        return json.dumps(False)
    return json.dumps(True)

@map('/api/task/addToList', authRequired=True)
def addToList(request):
    try:
        data = parseData(request, taskId=None, listId=None)
        if data.taskId:
            t = request.txn.query(Task).filter(Task.id==data.taskId).first()
            l = request.txn.query(List).filter(List.id==data.listId).first()
            l.addTask(t)
            t.log("added to list %s" %(l.name,), request.session.user)
    except Exception, e:
        return json.dumps(False)
    return json.dumps(True)


