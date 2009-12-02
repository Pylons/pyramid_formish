import unittest
from repoze.bfg import testing

class FormDirectiveTests(unittest.TestCase):
    def setUp(self):
        testing.cleanUp()

    def tearDown(self):
        testing.cleanUp()
        
    def _makeOne(self, context, controller_factory, **kw):
        from repoze.bfg.formish.zcml import FormDirective
        return FormDirective(context, controller_factory, **kw)

    def test_after(self):
        import webob
        import schemaish
        context = DummyZCMLContext()
        from repoze.bfg.view import render_view_to_response
        title = schemaish.String()
        factory = make_controller_factory(fields=[('title', title)])
        directive = self._makeOne(context, factory)
        directive._actions = [{'name':'submit','title':'title','validate':True}]
        directive.after()
        self.assertEqual(len(context.ac), 2)
        for action in context.ac:
            action['callable']()

        request = testing.DummyRequest()
        display = render_view_to_response(None, request, '')
        self.assertEqual(display, '123')

        request = testing.DummyRequest()
        request.params = webob.MultiDict()
        request.params['submit'] = True
        display = render_view_to_response(None, request, '')
        self.assertEqual(display, 'submitted')

class ActionDirectiveTests(unittest.TestCase):
    def setUp(self):
        testing.cleanUp()

    def tearDown(self):
        testing.cleanUp()

    def _callFUT(self, context, name, title=None, validate=True):
        from repoze.bfg.formish.zcml import action
        return action(context, name, title, validate)

    def test_with_title(self):
        context = DummyZCMLContext()
        context.context = DummyZCMLContext()
        actions = context.context._actions = []
        self._callFUT(context, 'name', title='title', validate=False)
        self.assertEqual(
            actions,
            [{'validate': False, 'name': 'name', 'title': 'title'}])
    
    def test_without_title(self):
        context = DummyZCMLContext()
        context.context = DummyZCMLContext()
        actions = context.context._actions = []
        self._callFUT(context, 'name', validate=False)
        self.assertEqual(
            actions,
            [{'validate': False, 'name': 'name', 'title': 'Name'}])
        
    
class TestFormView(unittest.TestCase):
    def _makeOne(self, controller_factory, action, actions, form_id=None):
        from repoze.bfg.formish.zcml import FormView
        return FormView(controller_factory, action, actions, form_id=form_id)

    def test_noname(self):
        import schemaish
        import validatish
        title = schemaish.String(validator=validatish.validator.Required())
        action = {'name':None, 'title':'cancel', 'validate':False}
        actions = [action]
        factory = make_controller_factory(fields=[('title', title)])
        view = self._makeOne(factory, action, actions)
        context = testing.DummyModel()
        request = testing.DummyRequest()
        result = view(context, request)
        self.assertEqual(result, '123')

    def test_formid(self):
        view = self._makeOne(None, {'name':1, 'validate':True}, None, 'default')
        self.assertEqual(view.form_id, 'default')

    def test_novalidate(self):
        import schemaish
        import validatish
        title = schemaish.String(validator=validatish.validator.Required())
        action = {'name':'cancel', 'title':'cancel', 'validate':False}
        actions = [action]
        factory = make_controller_factory(fields=[('title', title)])
        view = self._makeOne(factory, action, actions)
        context = testing.DummyModel()
        request = testing.DummyRequest()
        result = view(context, request)
        self.assertEqual(result, 'cancelled')
        self.assertEqual(request.form_action, 'cancel')

    def test_validate_no_error(self):
        import schemaish
        title = schemaish.String()
        action = {'name':'submit', 'title':'submit', 'validate':True}
        actions = [action]
        factory = make_controller_factory(fields=[('title', title)],
                                          defaults={'title':'the title'})
        view = self._makeOne(factory, action, actions)
        context = testing.DummyModel()
        request = testing.DummyRequest()
        result = view(context, request)
        self.assertEqual(result, 'submitted')
        self.assertEqual(request.form_action, 'submit')
        self.failUnless(request.form)
        self.failUnless(request.form_controller) 
        self.failUnless(request.form_defaults)
        self.failUnless(request.form_schema)
        self.failUnless(request.form_fields)
        self.failUnless(request.form_actions)
        self.assertEqual(dict(request.form.defaults), {'title':'the title'})

    def test_validate_form_error(self):
        import schemaish
        import validatish
        title = schemaish.String(validator=validatish.validator.Required())
        action = {'name':'submit', 'title':'submit', 'validate':True}
        actions = [action]
        factory = make_controller_factory(fields=[('title', title)],
                                          defaults={'title':'the title'})
        view = self._makeOne(factory, action, actions)
        context = testing.DummyModel()
        request = testing.DummyRequest()
        result = view(context, request)
        self.assertEqual(result, '123')
        self.assertEqual(request.form_action, 'submit')
        self.failUnless(request.form)
        self.failUnless(request.form_controller) 
        self.failUnless(request.form_defaults)
        self.failUnless(request.form_schema)
        self.failUnless(request.form_fields)
        self.failUnless(request.form_actions)
        self.assertEqual(dict(request.form.defaults), {'title':'the title'})
        self.failUnless('title' in request.form.errors)

    def test_validate_validation_error(self):
        import schemaish
        from repoze.bfg.formish import ValidationError
        title = schemaish.String()
        action = {'name':'submit', 'title':'submit', 'validate':True}
        actions = [action]
        factory = make_controller_factory(fields=[('title', title)],
                                          exception=ValidationError(title='a'),
                                          defaults={'title':'the title'})
        view = self._makeOne(factory, action, actions)
        context = testing.DummyModel()
        request = testing.DummyRequest()
        result = view(context, request)
        self.assertEqual(result, '123')
        self.assertEqual(request.form_action, 'submit')
        self.failUnless(request.form)
        self.failUnless(request.form_controller) 
        self.failUnless(request.form_defaults)
        self.failUnless(request.form_schema)
        self.failUnless(request.form_fields)
        self.failUnless(request.form_actions)
        self.assertEqual(dict(request.form.defaults), {'title':'the title'})
        self.failUnless('title' in request.form.errors)

    def test_selfvalidate(self):
        import schemaish
        import validatish
        action = {'name':'submit', 'title':'submit', 'validate':True}
        actions = [action]
        title = schemaish.String(validator=validatish.validator.Required())
        factory = make_controller_factory(selfvalidate=True,
                                          fields=[('title', title)])
        view = self._makeOne(factory, action, actions)
        context = testing.DummyModel()
        request = testing.DummyRequest()
        result = view(context, request)
        self.assertEqual(result, 'validated')

    def test_with_widgets(self):
        import schemaish
        import validatish
        import formish
        title = schemaish.String(validator=validatish.validator.Required())
        action = {'name':None, 'title':'cancel', 'validate':False}
        actions = [action]
        titlewidget = formish.Input()
        factory = make_controller_factory(fields=[('title', title)],
                                          widgets={'title':titlewidget})
        view = self._makeOne(factory, action, actions)
        context = testing.DummyModel()
        request = testing.DummyRequest()
        result = view(context, request)
        self.assertEqual(result, '123')
        

class TestAddTemplatePath(unittest.TestCase):
    def tearDown(self):
        testing.cleanUp()
        
    def _callFUT(self, context, path):
        from repoze.bfg.formish.zcml import add_template_path
        return add_template_path(context, path)

    def test_abspath(self):
        from repoze.bfg.formish.zcml import IFormishSearchPath
        from zope.component import getUtility
        import os.path
        here = os.path.dirname(__file__)
        abspath = os.path.abspath(here)
        context = DummyZCMLContext()
        self._callFUT(context, abspath)
        context.ac[0]['callable']()
        self.assertEqual(getUtility(IFormishSearchPath), [abspath])

    def test_pkg_relpath(self):
        from repoze.bfg.formish.zcml import IFormishSearchPath
        import repoze.bfg.formish.tests
        from zope.component import getUtility
        import os.path
        context = DummyZCMLContext(repoze.bfg.formish.tests)
        self._callFUT(context, 'fixtures')
        context.ac[0]['callable']()
        here = os.path.dirname(__file__)
        abspath = os.path.abspath(here)
        self.assertEqual(getUtility(IFormishSearchPath),
                         [os.path.join(abspath, 'fixtures')]
                          )

    def test_pkg_abspath(self):
        from repoze.bfg.formish.zcml import IFormishSearchPath
        import repoze.bfg.formish.tests
        from zope.component import getUtility
        import os.path
        context = DummyZCMLContext(repoze.bfg.formish.tests)
        self._callFUT(context, 'chameleon.formish.tests:fixtures')
        context.ac[0]['callable']()
        here = os.path.dirname(__file__)
        abspath = os.path.abspath(here)
        self.assertEqual(getUtility(IFormishSearchPath),
                         [os.path.join(abspath, 'fixtures')]
                          )
        
        
class DummyZCMLContext:
    info = None
    def __init__(self, resolved=None):
        self.resolved = resolved
        self.ac =[]
    def action(self, **kw):
        self.ac.append(kw)
    def resolve(self, package_name):
        return self.resolved

def make_controller_factory(fields=(), defaults=None, result='123',
                            widgets=None, selfvalidate=False, exception=None):
    class DummyController:
        def __init__(self, context, request):
            self.context = context
            self.request = request
        def form_fields(self):
            return fields
        def form_widgets(self, schema):
            if widgets is not None:
                return widgets
            return {}
        def __call__(self):
            return result
        def form_defaults(self):
            if defaults is None:
                return {}
            return defaults
        def handle_submit(self, converted):
            if exception:
                raise exception
            return 'submitted'
        def handle_cancel(self):
            return 'cancelled'
        if selfvalidate:
            def validate(self):
                return 'validated'

    return DummyController

