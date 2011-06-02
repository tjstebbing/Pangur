import json
from collections import namedtuple

from pangur import map

from .data import List, Task


def parseData(request, **args):
    X = namedtuple('X', args.keys())
    y = X(*args.values())
    try:
        return y._replace(**json.loads(request.form['data']))
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

@map('/api/tasksForList', authRequired=True)
def tasksForList(request):
    data = parseData(request, id=None)
    return encoder.encode(request.txn.query(List).filter(
        List.id==data.id).first().tasks)

@map('/api/list/update', authRequired=True)
def updateList(request):
#    try:
    data = parseData(request, id=None, name="Innominate List")
    if data.id:
        l = request.txn.query(List).filter(List.id==data.id).first()
        l.name = data.name
    else:
        l = List(data.name)
        request.txn.add(l)
        request.txn.flush()
#    except Exception, e:
#
#        return encoder.encode(False)
    return encoder.encode(l)

@map('/api/task/update', authRequired=True)
def updateTask(request):
    #try:
    data = parseData(request, id=None, text="", completed=None, 
                     listId=None)
    print data
    if data.id:
        t = request.txn.query(Task).filter(Task.id==data.id).first()
    else:
        t = Task(data.text, request.session.user)
        request.txn.add(t)
        t.log("created task", request.session.user)
    if data.completed is False:
        t.completed = False
        t.log("marked task as incomplete", request.session.user)
    elif data.completed is True:
        t.completed = True
        t.completedBy = request.session.user
        t.log("marked task as complete", request.session.user)
    if data.listId:
        print data
        request.txn.query(List).filter(List.id==data.id).first().addTask(t)
    #except Exception, e:
    #    print e
    #    return encoder.encode(False)
    return encoder.encode(t.id)

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
        return encoder.encode(False)
    return encoder.encode(True)


