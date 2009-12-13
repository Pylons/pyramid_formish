import os
import mako

import formish
from pkg_resources import resource_filename

from chameleon.zpt import language
from chameleon.zpt.template import PageTemplateFile
from zope.interface import Interface
from zope.component import queryUtility
from zope.component import getSiteManager

from repoze.bfg.settings import get_settings

def cache(func):
    def load(self, *args):
        template = self.registry.get(args)
        if template is None:
            self.registry[args] = template = func(self, *args)
        return template
    return load

class IFormishSearchPath(Interface):
    """ Utility interface representing a chameleon.formish search path """

class IFormishRenderer(Interface):
    """ Utility interface representing a formish renderer """
    
class TemplateLoader(object):
    parser = language.Parser()

    def __init__(self, search_path=None, auto_reload=False):
        if search_path is None:
            search_path = []
        if isinstance(search_path, basestring):
            search_path = [search_path]
        self.search_path = search_path
        self.auto_reload = auto_reload
        self.registry = {}
        self.notexists = {}

    @cache
    def load(self, filename):
        for path in self.search_path:
            path = os.path.join(path, filename)
            if (path in self.notexists) and (not self.auto_reload):
                raise mako.exceptions.TopLevelLookupException(
                    "Can not find template %s" % filename)
            try:
                return PageTemplateFile(path, parser=self.parser,
                                        auto_reload=self.auto_reload)
            except OSError:
                self.notexists[path] = True

        raise mako.exceptions.TopLevelLookupException(
            "Can not find template %s" % filename)

class ZPTRenderer(object):
    def __init__(self, directories=None):
        settings = get_settings()
        auto_reload = settings and settings['reload_templates'] or False
        if directories is None:
            directories = []
        if isinstance(directories, basestring):
            directories = [directories]
        self.directories = list(directories)
        # if there are ZCML-registered directories, use those too
        more = queryUtility(IFormishSearchPath, default=[])
        directories.extend(more)
        default = resource_filename('repoze.bfg.formish', 'templates/zpt')
        directories.append(default)
        self.loader = TemplateLoader(directories, auto_reload=auto_reload)

    def __call__(self, template, args):
        if template.startswith('/'):
            template = template[1:]
        template = self.loader.load(template)
        return template(**args)

def get_default_renderer():
    sm = getSiteManager()
    renderer = queryUtility(IFormishRenderer)
    if renderer is None:
        # register a default renderer
        renderer = ZPTRenderer()
        sm.registerUtility(renderer, IFormishRenderer)
    return renderer

class Form(formish.Form):
    def __init__(self, *arg, **kw):
        if not 'renderer' in kw:
            kw['renderer'] = get_default_renderer() # need to defer this til now
        formish.Form.__init__(self, *arg, **kw)

    def set_widget(self, title, widget):
        self[title].widget = widget
        
class ValidationError(Exception):
    def __init__(self, **errors):
        self.errors = errors
