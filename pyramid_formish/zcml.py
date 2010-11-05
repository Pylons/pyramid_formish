import os
from pkg_resources import resource_filename

from formish import validation
import schemaish

from zope.component import getSiteManager

import zope.configuration.config
from zope.configuration.fields import GlobalObject
from zope.configuration.exceptions import ConfigurationError

from zope.interface import Interface
from zope.interface import implements

from zope.schema import TextLine
from zope.schema import Bool

from pyramid.zcml import view

from pyramid_formish import Form
from pyramid_formish import ValidationError
from pyramid_formish import IFormishSearchPath
from pyramid.configuration import Configurator
from pyramid.threadlocal import get_current_registry

class IFormsDirective(Interface):
    view = GlobalObject(title=u'view', required=False)
    for_ = GlobalObject(title=u'for', required=False)
    name = TextLine(title=u'name', required=False)
    renderer = TextLine(title=u'renderer (template)', required=False)
    permission = TextLine(title=u'permission', required=False)
    containment = GlobalObject(title=u'containment', required=False)
    route_name = TextLine(title=u'route_name', required=False)
    wrapper = TextLine(title = u'wrapper', required=False)

class IFormDirective(Interface):
    controller = GlobalObject(title=u'display', required=True)
    for_ = GlobalObject(title=u'for', required=False)
    name = TextLine(title=u'name', required=False)
    renderer = TextLine(title=u'renderer (template)', required=False)
    permission = TextLine(title=u'permission', required=False)
    containment = GlobalObject(title=u'containment', required=False)
    route_name = TextLine(title=u'route_name', required=False)
    wrapper = TextLine(title = u'wrapper', required=False)
    form_id = TextLine(title = u'name', required=False)
    method = TextLine(title = u'method', required=False)

class IFormInsideFormsDirective(Interface):
    controller = GlobalObject(title=u'display', required=True)
    form_id = TextLine(title = u'name', required=True)

class FormsDirective(zope.configuration.config.GroupingContextDecorator):
    implements(zope.configuration.config.IConfigurationContext,
               IFormsDirective)

    def __init__(self, context, view=None, for_=None, name='', renderer=None,
                 permission=None, containment=None, route_name=None,
                 wrapper=None):
        self.context = context
        self.view = view
        self.for_ = for_
        self.name = name
        self.renderer = renderer
        self.permission = permission
        self.containment = containment
        self.route_name = route_name
        self.wrapper = wrapper
        self.forms = []

    def after(self):
        reg = get_current_registry()
        config = Configurator(reg, package=self.context.package)
        derived_view = config._derive_view(self.view) # XXX using a non-API

        def forms_view(context, request):
            forms = []
            for formdef in self.forms:
                formid = formdef.form_id
                actions = formdef._actions
                controller = formdef.controller(context, request)
                form = form_from_controller(controller, formid, actions)
                form.controller = controller
                form.bfg_actions = actions
                forms.append((formid, form))

            request.forms = [ x[1] for x in forms ]
            request_formid = request.params.get('__formish_form__')

            for formid, form in forms:
                if formid == request_formid:
                    for action in form.bfg_actions:
                        if action.name in request.params:
                            def curried_view():
                                return derived_view(context, request)
                            return submitted(request, form, form.controller,
                                             action, curried_view)

            return derived_view(context, request)

        view(self,
             permission=self.permission,
             for_=self.for_,
             view=forms_view,
             name=self.name,
             route_name=self.route_name,
             containment=self.containment,
             renderer=self.renderer,
             wrapper=self.wrapper)

class FormDirective(zope.configuration.config.GroupingContextDecorator):
    implements(zope.configuration.config.IConfigurationContext,
               IFormDirective)
    def __init__(self, context, controller, for_=None, name='',
                 renderer=None, permission=None, containment=None,
                 route_name=None, wrapper=None, form_id=None, method=None):
        self.context = context
        self.controller = controller
        self.for_ = for_
        self.name = name
        self.renderer = renderer
        self.permission  = permission
        self.containment = containment
        self.route_name = route_name
        self.wrapper = wrapper
        self.form_id = form_id
        method = method or 'POST'
        if method not in ('GET', 'POST'):
            raise ConfigurationError(
                'method must be one of "GET" or "POST" (not "%s")' % method)
        self.method = method
        self._actions = [] # mutated by subdirectives

    def after(self):
        if getattr(self.context, 'forms', None) is not None:
            self.context.forms.append(self)
            return
        
        display_action = FormAction(None)
        for action in [display_action] + self._actions:
            form_view = FormView(self.controller, action, self._actions,
                                 self.form_id, self.method)

            view(self,
                 permission=self.permission,
                 for_=self.for_,
                 view=form_view,
                 name=self.name,
                 request_param=action.name,
                 route_name=self.route_name,
                 containment=self.containment,
                 renderer=self.renderer,
                 wrapper=self.wrapper)

class FormView(object):
    def __init__(self, controller_factory, action, actions, form_id=None,
                 method='POST'):
        self.controller_factory = controller_factory
        self.action = action
        self.actions = actions
        self.form_id = form_id
        self.method = method

    def __call__(self, context, request):
        controller = self.controller_factory(context, request)
        form = form_from_controller(controller, self.form_id, self.actions,
                                    self.method)
        request.form = form

        if not self.action.name:
            # GET view
            return controller()

        # the result of a form submission
        return submitted(request, form, controller, self.action, controller)

def form_from_controller(controller, form_id, actions=(), method='POST'):
    form_schema = schemaish.Structure()

    form_fields = controller.form_fields()
    for fieldname, field in controller.form_fields():
        form_schema.add(fieldname, field)
    form = Form(form_schema, name=form_id, add_default_action=False,
                method=method)
    form.controller = controller

    for action in actions:
        form.add_action(action.name, action.title)

    form_widgets = []
    if hasattr(controller, 'form_widgets'):
        form_widgets = controller.form_widgets(form_fields)
        for name, widget in form_widgets.items():
            form[name].widget = widget

    defaults = None
    if hasattr(controller, 'form_defaults'):
        defaults = controller.form_defaults()
        form.defaults = defaults

    return form

def submitted(request, form, controller, action, view):
    handler = 'handle_%s' % action.name
    if action.validate:
        if hasattr(controller, 'validate'):
            result = controller.validate()
        else:
            try:
                converted = form.validate(request, check_form_name=False)
                if action.success:
                    result = action.success(controller, converted)
                else:
                    result = getattr(controller, handler)(converted)
            except validation.FormError, e:
                result = view()
            except ValidationError, e:
                for k, v in e.errors.items():
                    form.errors[k] = v
                result = view()
    else:
        result = getattr(controller, handler)()

    return result

class IActionDirective(Interface):
    """ The interface for an action subdirective """
    name = TextLine(title=u'name', required=True)
    title = TextLine(title=u'title', required=False)
    validate = Bool(title=u'validate', required=False, default=True)
    success = GlobalObject(title=u'success', required=False)

def action(context, name, title=None, validate=True, success=None):
    append = context.context._actions.append
    if title is None:
        title = name.capitalize()
    action = FormAction(name, title, validate, success)
    append(action)

class FormAction(object):
    def __init__(self, name, title=None, validate=True, success=None):
        self.name = name
        self.title = title
        self.validate = validate
        self.success = success
    
class IAddTemplatePath(Interface):
    """
    Directive for adding a new template path to the chameleon.formish
    renderer search path.
    """
    path = TextLine(
        title=u"Path spec",
        description=u'The spec of the template path.',
        required=True)

def add_template_path(context, path):
    if os.path.isabs(path):
        fullpath = path
    else:
        if ':' in path:
            package_name, path = path.split(':', 1)
        else:
            package_name = '.'
        package = context.resolve(package_name)
        name = package.__name__
        fullpath = resource_filename(name, path)

    def callback():
        sm = getSiteManager()
        search_path = sm.queryUtility(IFormishSearchPath, default=[])
        search_path.append(fullpath)
        sm.registerUtility(search_path, IFormishSearchPath)

    context.action(discriminator=None, callable=callback)

        
        
    
