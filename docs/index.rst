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
  :mod:`repoze.bfg.formish` "form controller".

``formish:form`` ZCML Directive
-------------------------------

When the ``meta.zcml`` of :mod:`repoze.bfg.formish` is included within
your :mod:`repoze.bfg` application, you can make use of the
``formish:form`` ZCML directive.  A ``formish:form`` configures one or
more special :mod:`repoze.bfg` "view" callables that render a form,
making use of a user-defined "form controller".

You must add the following to your application's ``configure.zcml`` to
use the ``formish:form`` directive:

.. code-block:: xml
   :linenos:

   <include package="repoze.bfg.formish" file="meta.zcml"/>

The ZCML directive requires Python code in the form of a *form
controller*.

You refer to the form controller within a ``formish:form`` directive
using the ``controller`` attribute, which is a dotted Python name
referring to the form controller class:

.. code-block:: xml
   :linenos:

   <formish:form
     for=".models.MyModel"
     name="add_community.html"
     renderer="templates/form_template.pt"
     controller=".forms.AddCommunityController"/>

The ``for``, ``name``, and ``renderer`` attributes of a
``formish:form`` tag mirror the meaning of the meanings of these names
in :mod:`repoze.bfg` ``view`` ZCML directive.  ``for`` represents the
class or interface which the context must implement for this view to
be invoked.  ``name`` is the view name.  ``renderer`` is the path to a
Chameleon ZPT template which will be used to render the form when it
is first presented, or redisplay the form with errors when form
validation fails.  The template is either a BFG "resource
specification" or an absolute or ZCML-package-relative path to an
on-disk template.

The above example assumes that there is a ``forms`` module which lives
in the same directory as the ``configure.zcml`` of your application,
and that it contains a form controller class named
``AddCommunityCommunityController``.  The ``controller`` attribute
names a *controller* for this form definition.  

Actions
-------

An *action* is a subdirective of the ``formish:form`` directive.  It
names a *handler*, a *param*, and a *title*.  For example:

.. code-block:: xml
   :linenos:

   <formish:form
     for=".models.MyModel"
     name="add_community.html"
     template="templates/form_template.pt"
     controller=".forms.AddCommunityController">

     <formish:action
       name="submit"
       title="Submit"
       />

     <formish:action
       name="cancel"
       title="Cancel"
       validate="false"
       />

   </formish:form>

Any number of ``formish:action`` tags can be present within a
``formish:form`` tag.

Each ``formish:action`` tag represents a submit button at the bottom
of a rendered form that will be given an HTML "value" matching the
``name`` attribute.  When this button is pressed, the value of
``name`` will be present in the ``request.params`` dictionary.  The
*value* of the button (the text visible to the user) will be the value
of the ``title`` attribute.

The ``name`` attribute of an action tag also represents the name of a
*handler* for an action.  Handlers are defined on form controller
classes as a method of the form controller class named
``handle_<actionname>``.  A handler method is invoked only when the
value of the ``param`` attribute for its action is present as a key in
the ``request.params`` dictionary *and* when the submission validates
properly (or when ``validate="false"`` is present in the action
definition).

Form Controllers
----------------

A *form controller* is a class which has the following
responsibilities:

- Provide the *default values* for the form's fields.

- Provide the *fields* used by the form.

- Provide the *widgets* used to render the form's fields.

- Provide a *display method* for the form.

- Provide one or more *handlers* for the form's actions after
  succesful validation.

A form controller may also (but commonly does not) provide a method
that does custom validation of a form submission.

Form Controller Constructor
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The constructor of a form controller class should accept two
arguments: ``context`` and ``request``.  The ``context`` is the BFG
context of the view which creates the form controller, and the
``request`` is the WebOb request object.  For example:

.. code-block:: python
   :linenos:

   from my.package import security

   class AddCommunityFormController(object):
       def __init__(self, context, request):
           self.context = context
           self.request = request
           self.workflow = security.get_workflow(context)

The constructor for a form controller is called whenever a request
that displays or validates a form is handled.  Like a view, a form
controller's lifecycle is no longer than the lifecycle of a single
request.

The imports and associated APIs defined in the examples above and
below are clearly fictional, but for purposes of example, we'll assume
that the ``my.package.security`` module offers an API which allows the
developer to determine whether a "workflow" is available for the
current context representing a dynamic set of choices based on the
current state of the context; furthermore it offers an API to see if
there are any valid security transitions for the current user
associated with this workflow.  This sort of thing is typical in a
content management system.  Although it is purely fictional, this
example hopefully demonstrates that we can influence both the form and
the schema as necessary based on a set of conditions in the handler's
initialization.

Providing Field Default Values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``form_defaults`` method of a form controller accepts no
arguments, and should return a dictionary mapping form field key to
Python value.

.. code-block:: python
   :linenos:

   from my.package import security

   class AddCommunityFormController(object):
       def __init__(self, context, request):
           self.context = context
           self.request = request
           self.workflow = security.get_workflow(context)

       def form_defaults(self):
           defaults = {
           'title':'',
           'tags': [], 
           'description':'',
           'text':'',
           }
           if self.workflow is not None:
               defaults['security_state']  = self.workflow.initial_state
           return defaults

If a form controller does not provide the ``form_defaults`` method, no
defaults are associated with the rendered form.

Providing Fields
~~~~~~~~~~~~~~~~

A form controller provides the *fields* of a form via its
``form_fields`` method.  If defined, it must return a sequence of
two-tuples.  Each tuple in the returned value should be of a certain
composition.  The first value in the tuple should be a string
containing the field name.  This should match the name supplied as a
dictionary key in the ``form_defaults`` method.  The second value in
the tuple should be a ``schemaish`` Structure object, such as a
``schemish.String`` or another data type.  These types of objects
often make use of :term:`validatish` validators.  For example:

.. code-block:: python
   :linenos:

   from my.package import security
   import schemaish
   import formish
   from validatish import validator

   tags_field = schemaish.Sequence(schemaish.String())

   description_field = schemaish.String(
       description=('This description will appear in search results and '
                    'on the community listing page.  Please limit your '
                    'description to 100 words or less'),
       validator=validator.All(validator.Length(max=500),
                                       validator.Required())
       )

   text_field =  schemaish.String(
       description=('This text will appear on the Overview page for this '
                    'community.  You can use this to describe the '
                    'community or to make a special announcement.'))

   security_field = schemaish.String(
       description=('Items marked as private can only be seen by '
                    'members of this community.'))

   class AddCommunityFormController(object):
       def __init__(self, context, request):
           self.context = context
           self.request = request
           self.workflow = security.get_workflow(context)

       def form_defaults(self):
           defaults = {
           'title':'',
           'tags': [], 
           'description':'',
           'text':'',
           }
           if self.workflow is not None:
               defaults['security_state']  = self.workflow.initial_state
           return defaults

       def form_fields(self):
           fields = [
              ('title', title_field),
              ('tags', tags_field),
              ('description', description_field),
              ('text', text_field),
              ]
           if self.workflow is not None and self.workflow.states:
               fields.append(('security_state', security_field))
           return fields

The structure returned by ``form_fields`` is the ordered set of data
types of fields associated with a form, as well as any validation
constraints for individual fields on the form.  Note that the actual
field objects it returns don't need to be reconstructed on every
request; they can be shared between requests, as in the above example.

A result of ``form_fields`` does not describe the user interface
elements associated with the fields it describes (this is the job of
*widgets*).

If a form controller does not supply a ``form_fields`` method, an
error is raised.

Providing Widgets
~~~~~~~~~~~~~~~~~

Widgets are associated with fields via the ``form_widgets`` method of
a form controller.  The ``form_widgets`` method accepts a list of
fields (this is really just the return value of the ``form_fields``
method of your form controller), and should return a dictionary.  Each
of the keys in the dictionary should be a field name, and the value
should be a Formish :term:`widget`.  For example:

.. code-block:: python
   :linenos:

   from my.package import security
   from my.package import widgets

   import schemaish
   import formish
   from validatish import validator

   tags_field = schemaish.Sequence(schemaish.String())

   description_field = schemaish.String(
       description=('This description will appear in search results and '
                    'on the community listing page.  Please limit your '
                    'description to 100 words or less'),
       validator=validator.All(validator.Length(max=500),
                                       validator.Required())
       )

   text_field =  schemaish.String(
       description=('This text will appear on the Overview page for this '
                    'community.  You can use this to describe the '
                    'community or to make a special announcement.'))

   security_field = schemaish.String(
       description=('Items marked as private can only be seen by '
                    'members of this community.'))

   class AddCommunityFormController(object):
       def __init__(self, context, request):
           self.context = context
           self.request = request
           self.workflow = security.get_workflow(context)

       def form_defaults(self):
           defaults = {
           'title':'',
           'tags': [], 
           'description':'',
           'text':'',
           }
           if self.workflow is not None:
               defaults['security_state']  = self.workflow.initial_state
           return defaults

       def form_fields(self):
           fields = [
              ('title', title_field),
              ('tags', tags_field),
              ('description', description_field),
              ('text', text_field),
              ]
           if self.workflow is not None and self.workflow.states:
               fields.append(('security_state', security_field))
           return fields

       def form_widgets(self, fields):
           widgets = {
             'title':formish.Input(),
             'description': formish.TextArea(cols=60, rows=10),
             'text':widgets.RichTextWidget(),
             }
           widgets['tags'] = karlwidgets.TagsAddWidget()
           schema = dict(fields)
           if 'security_state' in schema:
               security_states = self.workflow.states
               widgets['security_state'] = formish.RadioChoice(
                   options=[ (s['name'], s['title']) for s in security_states],
                   none_option=None)
           return widgets

If the form controller does not supply a ``form_widgets`` method, the
default Formish widgets for the schema's field types are used.  These
are defined by the Formish package itself.

Providing a Display Method
~~~~~~~~~~~~~~~~~~~~~~~~~~

The *display method* of a form controller is its ``__call__`` method.
The ``__call__`` method accepts no arguments.  It must return either a
dictionary or a WebOb *response* object.  If the display method
returns a dictionary, the *renderer* associated with the form
controller's ZCML statement will be used to render the dictionary to a
response.  Here's an example of a form controller with a display
method on it.

.. code-block:: python
   :linenos:

   from my.package import security
   from my.package import widgets
   from my.package import api

   import schemaish
   import formish
   from validatish import validator

   tags_field = schemaish.Sequence(schemaish.String())

   description_field = schemaish.String(
       description=('This description will appear in search results and '
                    'on the community listing page.  Please limit your '
                    'description to 100 words or less'),
       validator=validator.All(validator.Length(max=500),
                                       validator.Required())
       )

   text_field =  schemaish.String(
       description=('This text will appear on the Overview page for this '
                    'community.  You can use this to describe the '
                    'community or to make a special announcement.'))

   security_field = schemaish.String(
       description=('Items marked as private can only be seen by '
                    'members of this community.'))

   class AddCommunityFormController(object):
       def __init__(self, context, request):
           self.context = context
           self.request = request
           self.workflow = security.get_workflow(context)

       def form_defaults(self):
           defaults = {
           'title':'',
           'tags': [], 
           'description':'',
           'text':'',
           }
           if self.workflow is not None:
               defaults['security_state']  = self.workflow.initial_state
           return defaults

       def form_fields(self):
           fields = [
              ('title', title_field),
              ('tags', tags_field),
              ('description', description_field),
              ('text', text_field),
              ]
           if self.workflow is not None and self.workflow.states:
               fields.append(('security_state', security_field))
           return fields

       def form_widgets(self, fields):
           widgets = {
             'title':formish.Input(),
             'description': formish.TextArea(cols=60, rows=10),
             'text':widgets.RichTextWidget(),
             }
           widgets['tags'] = karlwidgets.TagsAddWidget()
           schema = dict(fields)
           if 'security_state' in schema:
               security_states = self.workflow.states
               widgets['security_state'] = formish.RadioChoice(
                   options=[ (s['name'], s['title']) for s in security_states],
                   none_option=None)
           return widgets

       def __call__(self):
           api = api.TemplateAPI(self.context, self.request)
           return {'api':api, 'page_title':'Edit %s' % self.context.title}

If there is no key in in ``request.params`` dictionary which matches
the ``param`` value of a particular ``formish:action`` associated with
a form, the ``__call__`` of the controller is called and the form is
displayed.  Likewise, if a form is submitted, and validation fails,
the ``__call__`` of the controller is called and the form is
redisplayed with errors.

For example, if the form we're defining above is invoked with a
request that has a params dict that has the value ``cancel`` as a key,
the ``handle_cancel`` method of the ``.forms.AddCommunityController``
handler will be called after validation is performed.  But if neither
``submit`` nor ``cancel`` is present in ``request.params``, the
``__call__`` method of the controller is called, and no validation is
performed.

If a form controller does not supply a ``__call__`` method, an error
is raised.

Providing Handlers
~~~~~~~~~~~~~~~~~~

Each *handler* of a form controller is responsible for returning a
response or a dictionary.  A *handler* of a form controller is called
after *validation* is performed successfully for an *action*.  Note
that these handlers are *not* called when form validation is
unsuccessful: when form validation is not successful the form display
method is called and the form is redisplayed with error messages.

Each handler has the method name ``handle_<action_name>``.  If the
``validate`` flag of a ``formish:action`` tag is ``true`` (the
default), the associated handler will accept a single argument named
``converted``.  If the ``validate`` tag is false, it will accept no
arguments.

For example, the ``cancel`` action of a ``formish:form`` ZCML
definition for a form controller (which is defined in ZCML as
``validate="false"`` might be defined as so:

.. code-block:: python
   :linenos:

   def handle_cancel(self):
       from webob.exc import HTTPFound
       return HTTPFound(location=model_url(self.context, self.request))

A more complex example, which provides the ``submit`` action for the
form we've been fleshing out so far is as follows (it is
``validate=true`` by default, so accepts a ``converted`` argument):

.. code-block:: python
   :linenos:

   def handle_submit(self, converted):
       from repoze.bfg.security import authenticated_userid
       from repoze.bfg.traversal import model_url
       from webob.exc import HTTPFound

       request = self.request
       context = self.context
       userid = authenticated_userid(request)
       community = create_content(ICommunity,
                                  converted['title'],
                                  converted['description'],
                                  converted['text'],
                                  userid,
                                  )
       # required to use moderators_group_name and
       # members_group_name
       community.__name__ = converted['title']
       community.tags = converted['tags']
       context[name] = community

       if self.workflow is not None:
           if 'security_state' in converted:
               self.workflow.transition_to_state(community, request,
                                                 converted['security_state'])
       location = model_url(community, request,
                            'members', 'add_existing.html',
                            query={'status_message':'Community added'})
       return HTTPFound(location=location)

The return value of the above example's handler is a "response" object
(an object which has the attributes ``app_iter``, ``headerlist`` and
``status``).  A handler is permitted to return a response or a
dictionary.  If it returns a dictionary, the ``template`` associated
with the form is rendered with the result of the dictionary in its
global namespace.

If a ``handle_<actionname>`` method for a form action does not exist
on a form controller as necessary, an error is raised at form
submission time.

A handler may also raise a ``repoze.bfg.formish.ValidationError``
exception if it detects a post-validation error.  This permits
"whole-form" validation that requires data that may only be known by
the handler at runtime.  When a handler raises such an error, the form
is rerendered with the error present in the rendering.  The error
should be raised with keyword arguments matching field names that map
to error messages, e.g.:

.. code-block:: python
   :linenos:

   from repoze.bfg.formish import ValidationError
   raise ValidationError(title='Wrong!')

If any validation error is raised, and a :term:`transaction` is in
play, the transaction is aborted.

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
