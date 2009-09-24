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
    display = GlobalObject(title=u'display', required=True)
    for_ = GlobalObject(title=u'for', required=False)
    name = TextLine(title=u'name', required=False)
    template = TextLine(title=u'template', required=False)
    permission = TextLine(title=u'permission', required=False)
    containment = GlobalObject(title=u'containment', required=False)
    route_name = TextLine(title=u'route_name', required=False)
    wrapper = TextLine(title = u'wrapper', required=False)

class FormDirective(zope.configuration.config.GroupingContextDecorator):
    implements(zope.configuration.config.IConfigurationContext,
               IFormDirective)
    def __init__(self, context, schema, display, for_=None, name='',
                 template=None, permission=None, containment=None,
                 route_name=None, wrapper=None):
        self.context = context
        self.schema = schema
        self.display = display
        self.for_ = for_
        self.name = name
        self.template = template
        self.permission  = permission
        self.containment = containment
        self.route_name = route_name
        self.wrapper = wrapper
        self._actions = [] # mutated by subdirectives

    def after(self):
        def form_show_view(context, request):
            schema = self.schema()
            form = Form(schema, add_default_action=False)
            for action in self._actions:
                form.add_action(action['param'], action['title'])
            defaults = {'form':form, 'schema':schema}
            request.schema = schema
            request.form = form
            result = self.display(context, request)
            if isinstance(result, dict):
                defaults.update(result)
            return defaults

        view(self.context,
             permission=self.permission,
             for_=self.for_,
             view=form_show_view,
             name=self.name,
             route_name=self.route_name,
             containment=self.containment,
             renderer=self.template,
             wrapper=self.wrapper)

        for action in self._actions:
            form_action_view = make_form_action_view(
                action, self._actions, self.schema, self.display)
            view(self.context,
                 permission=self.permission,
                 for_=self.for_,
                 view=form_action_view,
                 name=self.name,
                 route_name=self.route_name,
                 request_param=action['param'],
                 containment=self.containment,
                 renderer=self.template,
                 wrapper=self.wrapper)

def make_form_action_view(action, actions, schema, display):
    def form_action_view(context, request):
        this_schema = schema()
        form = Form(this_schema, add_default_action=False)
        for a in actions:
            form.add_action(a['param'], a['title'])
        request.form = form
        request.schema = schema
        request.converted = {}
        defaults = {'form':form, 'schema':schema}
        if action['validate']:
            try:
                converted = form.validate(request,check_form_name=False)
                request.converted = converted
                return action['success'](context, request)
            except validation.FormError, e:
                result = display(context, request)
                if result is None:
                    result = {}
                if isinstance(result, dict):
                    defaults.update(result)
                return defaults
            except ValidationError, e:
                for k, v in e.errors.items():
                    form.errors[k] = v
                result = display(context, request)
                if result is None:
                    result = {}
                if isinstance(result, dict):
                    defaults.update(result)
                return defaults
                    
        else:
            return action['success'](context, request)
    return form_action_view

class IActionDirective(Interface):
    """ The interface for an action subdirective """
    success = GlobalObject(title=u'success handler', required=True)
    param = TextLine(title=u'param', required=True)
    title = TextLine(title=u'title', required=False)
    validate = Bool(title=u'validate', required=False, default=True)

def action(context, success, param, title=None, validate=True):
    append = context.context._actions.append
    if title is None:
        title = param.capitalize()
    action = {'success':success, 'param':param, 'title':title,
              'validate':validate}
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

        
        
    
