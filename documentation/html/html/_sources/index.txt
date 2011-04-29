Documentation for the Pangur Project
====================================

What is Pangur?
---------------

Pangur is a simple micro-framework for the creation of WSGI applications, based
on the `Werkzeug WSGI library`_. In Pangur we have made some choices in terms of 
dependancies for things such as how to manage your data (`SQLAlchemy`_), how to 
handle templates (`Jinja`_),  and how you might deal with forms (`WTForms`_) etc. 
We have done this because the aim of Pangur is not to be a minimalistic helper 
utility for WSGI (Werkzeug already does this very well), but to be an easy to 
use micro-framework for getting things done in a way that gets out of your way 
as much as possible.

.. _Jinja: http://jinja.pocoo.org 
.. _Werkzeug WSGI library: http://werkzeug.pocoo.org 
.. _SQLAlchemy: http://sqlalchemy.org
.. _WTForms: http://wtforms.simplecodes.com/

Contents:

.. toctree::
   :maxdepth: 2

   introduction

