import os
from pkg_resources import resource_filename

from formish import validation

from zope.component import getSiteManager
import zope.configuration.config
from zope.configuration.fields import GlobalObject

from zope.interface import Interface
from zope.interface import implements

from zope.schema import TextLine

from repoze.bfg.zcml import view

from repoze.bfg.formish import Form
from repoze.bfg.formish import IFormishSearchPath

class IFormDirective(Interface):
    schema = GlobalObject(title=u'schema', required=True)
    renderer = TextLine(title=u'renderer', required=True)
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
    def __init__(self, context, schema, renderer, for_=None, name='',
                 template=None, permission=None, containment=None,
                 route_name=None, wrapper=None):
        self.context = context
        self.schema = schema
        self.renderer = renderer
        self.for_ = for_
        self.name = name
        self.template = template
        self.permission  = permission
        self.containment = containment
        self.route_name = route_name
        self.wrapper = wrapper
        self.actions = [] # mutated by subdirectives

    def after(self):
        def register():

            def form_show_view(context, request):
                schema = self.schema()
                form = Form(schema, add_default_action=False)
                for action in self.actions:
                    form.add_action(action['param'], action['title'])
                defaults = {'form':form, 'schema':schema}
                result = self.renderer(context, request, schema, form)
                if isinstance(result, dict):
                    defaults.update(result)
                return result
                    
            view(self.context,
                 permission=self.permission,
                 for_=self.for_,
                 view=form_show_view,
                 name=self.name,
                 route_name=self.route_name,
                 containment=self.containment,
                 renderer=self.template,
                 wrapper=self.wrapper)

            for action in self.actions:
                def form_action_view(context, request):
                    schema = self.schema()
                    form = Form(schema, add_default_action=False)
                    for action in self.actions:
                        form.add_action(action['param'], action['title'])
                    try:
                        converted = form.validate(request,check_form_name=False)
                        return action['success'](context, request, converted)
                    except validation.FormError:
                        defaults = {'form':form, 'schema':schema}
                        result = self.renderer(context, request, schema, form)
                        if isinstance(result, dict):
                            defaults.update(result)
                        return defaults
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
        self.action(
            discriminator = None,
            callable = register,
            )

class IActionDirective(Interface):
    """ The interface for an action subdirective """
    success = GlobalObject(title=u'success handler', required=True)
    param = TextLine(title=u'param', required=True)
    title = TextLine(title=u'title', required=False)

def action(context, success, param, title=None):
    append = context.context.actions.append
    if title is None:
        title = param.capitalize()
    action = {'success':success, 'param':param, 'title':title}
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

        
        
    
