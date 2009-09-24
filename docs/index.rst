Documentation for repoze.bfg.formish
====================================

:mod:`repoze.bfg.formish` is a package which provides
:mod:`repoze.bfg` bindings for the :term:`Formish` package, which is
an excellent form generation and validation package for Python.

This package provides:

- A ``chameleon.zpt`` Formish "renderer" class.

- A set of ``chameleon.zpt`` templates which implement the default
  Formish widgetset.

- A convenience ``Form`` implementation, which inherits from the
  standard ``formish.Form`` class, but uses the ``chameleon_zpt``
  renderer instead of the default Formish ``mako`` renderer.

- A ``formish:add_template_path`` ZCML directive which allows for the
  configuration of override Formish template locations.

- A ``formish:form`` ZCML directive which can be used to configure a
  Formish form "semi-declaratively".

Schemas
-------

Schemas are :term:`Schemaish` schema definitions, usually defined at
module scope as a class that inherits from the class
``schemaish.Structure``.  For example:

.. code-block:: python
   :linenos:

   import schemaish
   from validatish import validator

   class AddCommunitySchema(schemaish.Structure):
       title = schemaish.String(validator=validator.Required())
       description = schemaish.String(
           description = ('This description will appear in search results and '
                          'on the community listing page.  Please limit your '
                        ' description to 100 words or less'),
           validator = validator.All(validator.Length(max=500), 
                                     validator.Required())
           )
       text =  schemaish.String(
           description = ('This text will appear on the Overview page for this '
                         'community.  You can use this to describe the '
                         'community or to make a special announcement.'))
       tools = schemaish.Sequence(
           attr = schemaish.String(),
           description = 'Select which tools to enable on this community.')

A schema describes the data types of fields associated with a form, as
well as any validation constraints for individual fields on the form.
A schema does not describe the user interface elements associated with
the fields it describes.  Schemas are consulted by *forms*, which are
separate entities in the :term:`Formish` design.  A form is
responsible for describing the user interface associated with a
schema.

``formish:form`` ZCML Directive
-------------------------------

When the ``meta.zcml`` of :mod:`repoze.bfg.formish` is included
within your :mod:`repoze.bfg` application, you can make use of the
``formish:form`` ZCML directive.  The ZCML directive uses two major
concepts: schemas and actions.

You must add the following to your application's ``configure.zcml`` to
use the ``formish:form`` directive:

.. code-block:: xml
   :linenos:

   <include package="repoze.bfg.formish" file="meta.zcml"/>

You refer to the schema defined in a Python within a ``formish:form``
directive using the ``schema`` attribute, which is a dotted Python
name referring to the schema class:

.. code-block:: xml
   :linenos:

   <formish:form
     for=".models.MyModel"
     name="add_community.html"
     schema=".forms.AddCommunitySchema"
     template="templates/form_template.pt"
     handler=".forms.Show"/>

A ``formish:form`` configures one or more special :mod:`repoze.bfg`
"view" callables that render a form.

The ``for`` and ``name`` attributes of a ``formish:form`` tag mirror
the meaning of the meanings of these names in :mod:`repoze.bfg`
``view`` ZCML directive.  ``for`` represents the class or interface
which the context must implement for this view to be invoked.
``name`` is the view name.

The above example assumes that there is a ``forms`` module which lives
in the same directory as the ``configure.zcml`` of your application,
and that it contains a schema definition named ``AddCommunitySchema``.
This is the value represented by the ``schema`` attribute above.

It also names a Chameleon ZPT template via its ``template`` attribute
which will be used to render the form when it is first presented, or
when form validation fails.  The template is either a BFG "resource
specification" or an absolute or ZCML-package-relative path to an
on-disk template.

The ``handler`` attribute names a "default" *handler* for this form
definition.  The definition of a *handler* is discussed below; for now
please assume it is a dotted Python name which specifies a special
kind of callable.  The above example names it as ``.forms.Show``,
which makes the assumption that a handler callable named ``Show``
lives in the package containing the ``configure.zcml`` file in a
module named ``forms``.
     
Actions
-------

An *action* is a subdirective of the ``formish:form`` directive.  It
names a *handler*, a *param*, and a *title*.  For example:

.. code-block:: xml
   :linenos:

   <formish:form
     for=".models.MyModel"
     name="add_community.html"
     schema=".forms.AddCommunitySchema"
     template="templates/form_template.pt"
     handler=".forms.Show">

     <action
       handler=".forms.Cancel"
       param="form_cancel"
       title="Cancel"
       />

   </formish:form>

Any number of ``action`` tags can be present within a ``formish:form``
tag.

Each ``action`` tag represents a submit button at the bottom of the
form that will be given an HTML "value" matching the ``param``
attribute.  When this button is pressed, the value of ``param`` will
be present in the ``request.params`` dictionary.  The *value* of the
button (the text visible to the user) will be the value of the
``title`` attribute.

Each action additionally must specify a ``handler`` attribute, which
is the dotted Python to a *factory* which has the capability to
influence the painting of the form as well as what happens when form
validation succeeds.  A particular handler is invoked only when the
value of the ``param`` attribute for its action is present as a key in
the ``request.params`` dictionary.

If there is no key in in ``request.params`` dictionary which matches
the ``param`` of a particular form's action, the handler of the form
itself is called.  For example, if the form we're defining above is
invoked with a request has a params dict that has the value
``form_cancel``, the ``.forms.Cancel`` handler is called.  But if
``form_cancel`` is not present, the ``.forms.Show`` handler is called.

Handlers
--------

A :term:`handler` is the dotted name to a Python callable which must
accept four arguments: ``context``, ``request``, ``schema`` and
``form``.  It must *return* a callable object which must accept a
single argument: ``converted``, which will be a dictionary represented
the values present in the form post when form validation was
successful.  The callable object which a handler returns is called
when form validation succeeds.  It is known as the *success* or
*success callable*.  A handler is usually represented a class, with
its ``__init__`` method representing the initialization, and its
``__call__`` method representing the success callable.  For example:

.. code-block:: python
   :linenos:

   from webob.exc import HTTPFound
   from repoze.bfg.url import model_url

   class Cancel(object):
       def __init__(self, context, request, schema, form):
           self.context = context
           self.request = request
           self.schema = schema
           self.form = form

       def __call__(self, converted):
           return HTTPFound(location=model_url(self.context, request))

The above handler does very little.  Its *success* (represented by its
``__call__`` method) just redirects back to the base URL of the
context object.

A handler needn't be a class.  The above handler could be equivalently
written as a function:

.. code-block:: python
   :linenos:

   from webob.exc import HTTPFound
   from repoze.bfg.url import model_url

   def Cancel(context, request, schema, form):
       def success(converted):
           return HTTPFound(location=model_url(context, request))
       return success

The return value of the above example's *success* is a "response"
object (an object which has the attributes ``app_iter``,
``headerlist`` and ``status``).  A handler's *success* is permitted to
return a response or a dictionary.  If it returns a dictionary, the
``template`` associated with the form is rendered with the result of
the dictionary in its global namespace.  For example:

.. code-block:: python
   :linenos:

   from repoze.bfg.url import model_url
   from api import TemplateAPI

   class Show(object):
       def __init__(self, context, request, schema, form):
           self.context = context
           self.request = request
           self.schema = schema
           self.form = form

       def __call__(self, converted):
           return {'api':TemplateAPI(self.context, self.request)}

A *success* object may also raise a ``schemaish.Invalid`` exception if
it detects a post-validation error.  This permits "whole-form"
validation that requires data that may only be known by the handler at
runtime.

.. code-block:: python
   :linenos:

   from repoze.bfg.url import model_url
   from api import TemplateAPI
   import schemaish

   class Show(object):
       def __init__(self, context, request, schema, form):
           self.context = context
           self.request = request
           self.schema = schema
           self.form = form

       def __call__(self, converted):
           raise schemaish.Invalid({'title':"I don't like this title"})

When a success raises a schemaish.Invalid error, the form is
rerendered with the error present in the rendering.

Influencing the Rendering of a Form With a Handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The examples of handlers we've seen so far do very little to influence
form rendering.  By default, Formish will render a very basic default
form for a given schema, which is almost never adequate for real-world
use.  Usually it is necessary to associate *defaults* and *widgets*
with a form.  Here's a fairly complicated example that does just that:

.. code-block:: python
   :linenos:

   from repoze.bfg.url import model_url
   from api import TemplateAPI
   import security
   import widgets
   import formish

   class Add(object):
       def __init__(self, context, request, schema, form):
           defaults = {
               'title':'',
               'description':'',
               'text':'',
               }

           form['title'].widget = formish.Input()
           form['description'].widget = formish.TextArea(cols=60, rows=10)
           form['text'].widget = widgets.RichTextWidget()

           workflow = security.get_workflow(context)

           if workflow is not None:
               security_states = security.get_security_states(workflow, request)
               if security_states:
                   field = schemaish.String(
                       description=('Private items can only be viewed by '
                                    'members of this community.'))
                   schema.attrs.insert(4, ('security_state', field))
                   defaults['security_state'] = workflow.initial_state
                   form['security_state'].widget = formish.RadioChoice(
                       options=[(s['name'],s['title']) for s in security_states],
                       none_option=None)

           form.defaults = defaults
           self.context = context
           self.request = request
           self.workflow = workflow

       def __call__(self):
           return {'api':TemplateAPI(self.context, self.request)}

Note that the above example mutates both the *form* and the *schema*.
It adds *defaults* to the form, representing the data that will end up
in the widgets if the form is rendered "cleanly".  It associates
widgets with particular form fields using the pattern ``form['name'] =
SomeWidget()``.  This allows for customization of the form
presentation using Formish "widgets".  It also mutates the schema,
adding an additional field to the schema if there is a valid
"workflow".

The imports and associated APIs defined in this module are clearly
fictional, but for purposes of example, we'll assume that the
``security`` module offers an API which allows the developer to
determine whether a "workflow" is available for the current context
representing a dynamic set of choices based on the current state of
the context; furthermore it offers an API to see if there are any
valid security transitions for the current user associated with this
workflow.  This sort of thing is typical in a content management
system.  Although it is purely fictional, this example hopefully
demonstrates that we can influence both the form and the schema as
necessary based on a set of conditions in the handler's
initialization.

The class name of the above example handler is ``Add``.  This is
because it's meant to represent the handler of an action which is
invoked when a user submits an add form by clicking on the button that
represents a submit action title.  Normally, such a handler would add
piece of content to the system.  But currently it doesn't do anything
interesting on "success"; its ``__call__`` method returns a dictionary
and rerenders the template.  We can change its ``__call__`` method to
do something more interesting when the form is submitted:

.. code-block:: python
   :linenos:

   from repoze.bfg.url import model_url
   import content
   import security
   import formish
   import schemaish
   import widgets
   from repoze.bfg.formish import ValidationError

   class Add(object):
       def __init__(self, context, request, schema, form):

           defaults = {
               'title':'',
               'description':'',
               'text':'',
               }

           form['title'].widget = formish.Input()
           form['description'].widget = formish.TextArea(cols=60, rows=10)
           form['text'].widget = widgets.RichTextWidget()

           workflow = security.get_workflow(context)
           if workflow is not None:
               security_states = security.get_security_states(workflow, request)
               if security_states:
                   field = schemaish.String(
                       description=('Private items can only be viewed by '
                                    'members of this community.'))
                   schema.attrs.insert(4, ('security_state', field))
                   defaults['security_state'] = workflow.initial_state
                   form['security_state'].widget = formish.RadioChoice(
                       options=[(s['name'],s['title']) for s in security_states],
                       none_option=None)

            form.defaults = defaults
            self.context = context
            self.request = request
            self.workflow = workflow

       def __call__(self, converted):
           title = converted['title']
           description = converted['description']
           text = converted['text']
           if title in self.context:
               msg = '%s already exists in the context' % title
               raise schemaish.Invalid({'title':msg})
           entry = content.make_entry(title, description, text)
           self.context[title] = entry
           if self.workflow is not None:
               if 'security_state' in converted:
                   self.workflow.transition(entry, self.request,
                                            converted['security_state'])
           location = model_url(self.context, self.request)
           return HTTPFound(location=location)

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
