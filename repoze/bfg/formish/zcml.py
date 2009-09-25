import os
from pkg_resources import resource_filename

from formish import validation

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
    schema = GlobalObject(title=u'schema', required=True)
    controller = GlobalObject(title=u'display', required=True)
    for_ = GlobalObject(title=u'for', required=False)
    name = TextLine(title=u'name', required=False)
    renderer = TextLine(title=u'renderer (template)', required=False)
    permission = TextLine(title=u'permission', required=False)
    containment = GlobalObject(title=u'containment', required=False)
    route_name = TextLine(title=u'route_name', required=False)
    wrapper = TextLine(title = u'wrapper', required=False)

class FormDirective(zope.configuration.config.GroupingContextDecorator):
    implements(zope.configuration.config.IConfigurationContext,
               IFormDirective)
    def __init__(self, context, schema, controller, for_=None, name='',
                 renderer=None, permission=None, containment=None,
                 route_name=None, wrapper=None):
        self.context = context
        self.schema = schema
        self.controller = controller
        self.for_ = for_
        self.name = name
        self.renderer = renderer
        self.permission  = permission
        self.containment = containment
        self.route_name = route_name
        self.wrapper = wrapper
        self._actions = [] # mutated by subdirectives

    def after(self):
        display_action = {'name':None, 'validate':False, 'title':None}
        for action in [display_action] + self._actions:
            form_view = make_form_view(action, self._actions,
                                       self.schema, self.controller)
            view(self.context,
                 permission=self.permission,
                 for_=self.for_,
                 view=form_view,
                 name=self.name,
                 request_param=action['name'],
                 route_name=self.route_name,
                 containment=self.containment,
                 renderer=self.renderer,
                 wrapper=self.wrapper)

def make_form_view(action, actions, schema_factory, controller_factory):
    validate = action['validate']
    name = action['name']
    title = action['title']
    def form_view(context, request):
        schema = schema_factory()
        form = Form(schema, add_default_action=False)
        for a in actions:
            form.add_action(a['name'], a['title'])
        controller = controller_factory(context, request)
        if hasattr(controller, 'defaults'):
            defaults = controller.defaults()
            form.defaults = defaults
        if hasattr(controller, 'setup'):
            controller.setup(schema, form)
        request.controller = controller
        request.schema = schema
        request.form = form
        request.action_name = name
        if name:
            handler = 'handle_%s' % name
            if validate:
                if hasattr(controller, 'validate'):
                    result = controller.validate()
                else:
                    try:
                        converted = form.validate(request,check_form_name=False)
                        result = getattr(controller, handler)(converted)
                    except validation.FormError, e:
                        result = controller()
                    except ValidationError, e:
                        for k, v in e.errors.items():
                            form.errors[k] = v
                        result = controller()
            else:
                result = getattr(controller, handler)()
        else:
            result = controller()
        return result
    return form_view

class IActionDirective(Interface):
    """ The interface for an action subdirective """
    name = TextLine(title=u'name', required=True)
    title = TextLine(title=u'title', required=False)
    validate = Bool(title=u'validate', required=False, default=True)

def action(context, name, title=None, validate=True):
    append = context.context._actions.append
    if title is None:
        title = name.capitalize()
    action = {'name':name, 'title':title, 'validate':validate}
    append(action)
    
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

        
        
    
