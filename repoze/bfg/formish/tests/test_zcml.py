import unittest
from repoze.bfg import testing

class FormDirectiveTests(unittest.TestCase):
    def setUp(self):
        testing.cleanUp()

    def tearDown(self):
        testing.cleanUp()
        
    def _makeOne(self, context, schema, controller, **kw):
        from repoze.bfg.formish.zcml import FormDirective
        return FormDirective(context, schema, controller, **kw)

    def test_after(self):
        import webob
        import schemaish
        context = DummyZCMLContext()
        from repoze.bfg.view import render_view_to_response
        class DummySchema(schemaish.Structure):
            title = schemaish.String()
        directive = self._makeOne(context, DummySchema, DummyController)
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
        
    
class TestMakeFormView(unittest.TestCase):
    def _callFUT(self, action, actions, schema_factory, controller_factory):
        from repoze.bfg.formish.zcml import make_form_view
        return make_form_view(action, actions, schema_factory,
                              controller_factory)

    def test_noname(self):
        import schemaish
        import validatish
        class DummySchema(schemaish.Structure):
            title = schemaish.String(validator=validatish.validator.Required())
        action = {'name':None, 'title':'cancel', 'validate':False}
        actions = [action]
        view = self._callFUT(action, actions, DummySchema, DummyController)
        context = testing.DummyModel()
        request = testing.DummyRequest()
        result = view(context, request)
        self.assertEqual(result, '123')

    def test_novalidate(self):
        import schemaish
        import validatish
        class DummySchema(schemaish.Structure):
            title = schemaish.String(validator=validatish.validator.Required())
        action = {'name':'cancel', 'title':'cancel', 'validate':False}
        actions = [action]
        view = self._callFUT(action, actions, DummySchema, DummyController)
        context = testing.DummyModel()
        request = testing.DummyRequest()
        result = view(context, request)
        self.assertEqual(result, 'cancelled')
        self.assertEqual(request.action_name, 'cancel')

    def test_validate_no_error(self):
        import schemaish
        class DummySchema(schemaish.Structure):
            title = schemaish.String()
        action = {'name':'submit', 'title':'submit', 'validate':True}
        actions = [action]
        view = self._callFUT(action, actions, DummySchema, DummyController)
        context = testing.DummyModel()
        request = testing.DummyRequest()
        result = view(context, request)
        self.assertEqual(result, 'submitted')
        self.assertEqual(request.action_name, 'submit')
        self.failUnless(request.form)
        self.failUnless(request.schema) 
        self.failUnless(request.controller) 
        self.assertEqual(dict(request.form.defaults), {'title':'the title'})
        self.assertEqual(request.controller.setup_called, True)

    def test_validate_form_error(self):
        import schemaish
        import validatish
        class DummySchema(schemaish.Structure):
            title = schemaish.String(validator=validatish.validator.Required())
        action = {'name':'submit', 'title':'submit', 'validate':True}
        actions = [action]
        view = self._callFUT(action, actions, DummySchema, DummyController)
        context = testing.DummyModel()
        request = testing.DummyRequest()
        result = view(context, request)
        self.assertEqual(result, '123')
        self.assertEqual(request.action_name, 'submit')
        self.failUnless(request.form)
        self.failUnless(request.schema) 
        self.failUnless(request.controller) 
        self.assertEqual(dict(request.form.defaults), {'title':'the title'})
        self.assertEqual(request.controller.setup_called, True)
        self.failUnless('title' in request.form.errors)

    def test_validate_validation_error(self):
        import schemaish
        import validatish
        from repoze.bfg.formish import ValidationError
        class DummySchema(schemaish.Structure):
            title = schemaish.String(validator=validatish.validator.Required())
        action = {'name':'submit', 'title':'submit', 'validate':True}
        actions = [action]
        view = self._callFUT(action, actions, DummySchema, DummyController)
        context = testing.DummyModel()
        request = testing.DummyRequest()
        request.exception = ValidationError
        result = view(context, request)
        self.assertEqual(result, '123')
        self.assertEqual(request.action_name, 'submit')
        self.failUnless(request.form)
        self.failUnless(request.schema) 
        self.failUnless(request.controller) 
        self.assertEqual(dict(request.form.defaults), {'title':'the title'})
        self.assertEqual(request.controller.setup_called, True)
        self.failUnless('title' in request.form.errors)

    def test_selfvalidate(self):
        import schemaish
        import validatish
        action = {'name':'submit', 'title':'submit', 'validate':True}
        actions = [action]
        class DummyValidatingController(DummyController):
            def validate(self):
                return 'validated'
        class DummySchema(schemaish.Structure):
            title = schemaish.String(validator=validatish.validator.Required())
        view = self._callFUT(action, actions, DummySchema,
                             DummyValidatingController)
        context = testing.DummyModel()
        request = testing.DummyRequest()
        result = view(context, request)
        self.assertEqual(result, 'validated')

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

class DummyController:
    def __init__(self, context, request):
        self.context = context
        self.request = request
    def setup(self, schema, form):
        self.setup_called = True
    def __call__(self):
        return '123'
    def defaults(self):
        return {'title':'the title'}
    def handle_submit(self, converted):
        if hasattr(self.request, 'exception'):
            raise self.request.exception
        return 'submitted'
    def handle_cancel(self):
        return 'cancelled'
