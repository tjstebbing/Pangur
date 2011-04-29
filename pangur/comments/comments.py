from datetime import datetime
import json, collections

import sqlalchemy as sa
import wtforms as wt

from pangur import exceptions
from pangur.database import rel, backref, orMap, DBMeta
from pangur.utils import registerForm, map, timesince
from pangur.users import User


commentsTable = sa.Table('comments', DBMeta,
                        sa.Column('id', sa.Integer, primary_key=True),
                        sa.Column('user_id', sa.Integer, sa.ForeignKey("users.id"),
                                  nullable=False),
                        sa.Column('subject_kind', sa.String),
                        sa.Column('subject_id', sa.Integer),
                        sa.Column('parent_id', sa.Integer),
                        sa.Column('created_on', sa.DateTime),
                        sa.Column('deleted', sa.Boolean, default=False),
                        sa.Column('mood', sa.String),
                        sa.Column('text', sa.String))


@orMap(commentsTable, properties={
       'user': rel(User),
    })
class Comment(object):

    def __init__(self, user_id, text, parent_id=None, subject_kind=None,
                                                      subject_id=None):
        self.user_id = user_id
        self.created_on = datetime.now()
        self.text = text
        if parent_id:
            self.parent_id = parent_id
        if subject_kind:
            self.subject_kind = subject_kind
        if subject_id:
            self.subject_id = subject_id

    @property
    def timesince(self):
        return timesince(self.created_on)


@map('/api/comment/<path:id>/delete')
def deleteComment(request):
    c = request.txn.query(Comment).filter(
        Comment.id==request.matches["id"]).first()
    if request.session.authenticated:
        if request.session.user == c.user:
            c.deleted = True
    request.response.data = json.dumps(c.deleted)


@map('/api/comment/<path:id>/info')
def getCommentInfo(request):
    c = request.txn.query(Comment).filter(
        Comment.id==request.matches["id"]).first()
    out = {
        "id" : c.id,
        "user" : c.user.username,
        "parent_id" : c.parent_id,
        "mood" : c.mood,
        "ago" : timesince(c.created_on),
        "deleted" : c.deleted,
        "actions" : [] }
    if request.session.authenticated:
        if not c.deleted:
            out['actions'].append('reply')
            if request.session.user == c.user:
                out['actions'].append('delete')
                out['actions'].append('edit')
    request.response.data = json.dumps(out)


def assembleComments(comments):

    d = collections.defaultdict(list)
    for c in comments:
        d[c.parent_id].append(c)

    out = []

    def walk(id, depth):
        print id, depth
        d[id].sort(key=lambda c: c.created_on)
        for child in d[id]:
            out.append(child)
            child.indent = depth
            walk(child.id, depth + 1)

    walk(None, 0)
    print [(c, c.id) for c in out]
    return out


def queryCommentsFor(request, subject_kind, subject_id):
    """Find all comments for one subject."""
    return request.txn.query(Comment).filter_by(
        subject_kind=subject_kind).filter_by(
        subject_id=subject_id).first()


def sortedCommentsFor(request, subject_kind, subject_id):
    """Get all comments for one subject, sorted for display."""
    return assembleComments(queryCommentsFor(request, subject_kind, subject_id))


@registerForm
class AddCommentForm(wt.Form):
    text = wt.TextAreaField("BBCode")

def handleForms(request, subject_kind, subject_id):
    #handle adding a comment
    if request.method == 'POST':
        f = request.forms.load('AddCommentForm')
        if f.validate():
            c = Comment(request.session.user.id, f.text.data,
                        subject_kind=subject_kind, subject_id=subject_id)
            request.txn.add(c)
            request.txn.flush()
            raise exceptions.RedirectException(request.relative('.', hash="c%s"%(c.id,)))

    #handle deleting a comment
    if 'delComment' in request.args:
        c = request.txn.query(Comment).filter_by(
            subject_kind=subject_kind).filter_by(
            subject_id=subject_id).filter(
            Comment.id == request.args['delComment']).first()
        if c:
            c.deleted = True
        raise exceptions.RedirectException(
            request.relative('.', hash="c%s"%(c.id,)))


map('/test/comments', 'comment_test.html')
