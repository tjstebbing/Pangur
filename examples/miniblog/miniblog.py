from datetime import datetime

import sqlalchemy as sa
import wtforms as wt

from pangur.utils import map, registerForm, slugify, populateFromForm
from pangur.database import orMap, DBMeta, rel
from pangur.users import User


#Create an sqlalchemy table to store entries in
entriesTable = sa.Table(
    'entries', DBMeta,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('user_id', sa.Integer, sa.ForeignKey("users.id"),
              nullable=False),
    sa.Column('title', sa.String),
    sa.Column('content', sa.String),
    sa.Column('slug', sa.String),
    sa.Column('created', sa.DateTime))


@orMap(entriesTable, properties={'user': rel(User)})
class Entry(object):
    """An Entry represents a writing on our blog and is mapped to
    the entriesTable, a relationship is also established with a user
    as the author of the entry, with a back-reference added to the
    user to fetch all entries for any given user.
    """

    def __init__(self, userID):
        self.user_id = userID
        self.created = datetime.now()


@registerForm
class EntryEditForm(wt.Form):
    """This is a form for creating and editing an Entry, notice
    that we decorate it with registerForm so that it is available
    on the request and to templates."""
    title = wt.TextField("Title", [wt.validators.length(max=100),
                                   wt.validators.required()])
    content = wt.TextAreaField("Content")


# Add a page which handles adding new entries, only available to
# authenticated users
@map('/newEntry', 'edit.html')#, authRequired=True)
def newEntry(request):
    if request.method == 'POST': #saving the form
        form = request.forms.load('EntryEditForm')
        if form.validate():
            entry = Entry(request.session.user.id)
            populateFromForm(form, entry, ('title','content'))
            entry.slug = slugify(entry.title)
            request.txn.add(entry)
            raise exceptions.RedirectException(request.relative('..'))


@map('/', 'entries.html')
def entries(request):
    return {'entries' : 'woo'}
