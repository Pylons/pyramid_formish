import os
from pkg_resources import resource_filename

from formish import validation
import schemaish

from zope.component import getSiteManager
import zope.configuration.config
from zope.configuration.fields import GlobalObject

from zope.interface import Interface
from zope.interface import implements

from zope.schema import TextLine
from zope.schema import Bool

from repoze.bfg.zcml import view

from repoze.bfg.formish import Form
from repoze.bfg.formish import ValidationError
from repoze.bfg.formish import IFormishSearchPath

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

class FormDirective(zope.configuration.config.GroupingContextDecorator):
    implements(zope.configuration.config.IConfigurationContext,
               IFormDirective)
    def __init__(self, context, controller, for_=None, name='',
                 renderer=None, permission=None, containment=None,
                 route_name=None, wrapper=None, form_id=None):
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
        self._actions = [] # mutated by subdirectives

    def after(self):
        display_action = FormAction(None)
        for action in [display_action] + self._actions:
            form_view = FormView(self.controller, action, self._actions,
                                 self.form_id)
            view(self.context,
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
    def __init__(self, controller_factory, action, actions, form_id=None):
        self.controller_factory = controller_factory
        self.action = action
        self.actions = actions
        self.form_id = form_id
        self.form_action = action
        self.form_actions = actions

    def __call__(self, context, request):
        form_action = request.form_action = self.form_action
        form_controller = self.controller_factory(context, request)
        request.form_controller = form_controller
        form_schema = schemaish.Structure()
        request.form_schema = form_schema

        form_fields = form_controller.form_fields()
        for fieldname, field in form_controller.form_fields():
            form_schema.add(fieldname, field)
        request.form_fields = form_fields

        form = Form(form_schema, add_default_action=False, name=self.form_id)
        request.form = form

        for action in self.form_actions:
            form.add_action(action.name, action.title)

        request.form_actions = self.form_actions

        form_widgets = []
        if hasattr(form_controller, 'form_widgets'):
            form_widgets = form_controller.form_widgets(form_fields)
            for name, widget in form_widgets.items():
                form[name].widget = widget
        request.form_widgets = form_widgets

        defaults = None
        if hasattr(form_controller, 'form_defaults'):
            defaults = form_controller.form_defaults()
            form.defaults = defaults
        request.form_defaults = defaults

        if not form_action.name:
            return form_controller()

        handler = 'handle_%s' % form_action.name
        if self.form_action.validate:
            if hasattr(form_controller, 'validate'):
                result = form_controller.validate()
            else:
                try:
                    converted = form.validate(request, check_form_name=False)
                    result = getattr(form_controller, handler)(converted)
                except validation.FormError, e:
                    result = form_controller()
                except ValidationError, e:
                    for k, v in e.errors.items():
                        form.errors[k] = v
                    result = form_controller()
        else:
            result = getattr(form_controller, handler)()

        return result

class IActionDirective(Interface):
    """ The interface for an action subdirective """
    name = TextLine(title=u'name', required=True)
    title = TextLine(title=u'title', required=False)
    validate = Bool(title=u'validate', required=False, default=True)

def action(context, name, title=None, validate=True):
    append = context.context._actions.append
    if title is None:
        title = name.capitalize()
    action = FormAction(name, title, validate)
    append(action)

class FormAction(object):
    def __init__(self, name, title=None, validate=True):
        self.name = name
        self.title = title
        self.validate = validate
    
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

        
        
    
