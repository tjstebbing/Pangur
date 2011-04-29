"""
Comments plugin.

This plugin renders a comments section on a page,
allowing users to post and reply to comments.
"""

from pangur import utils

utils.registerTemplates(__file__, 'templates')
utils.registerStatic(__file__, 'static')


# comments api.
from .comments import (
    Comment, commentsTable,
    queryCommentsFor, sortedCommentsFor, assembleComments,
    AddCommentForm, handleForms
)
