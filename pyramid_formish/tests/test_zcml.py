import unittest
from pyramid import testing

class FormsDirectiveTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _makeOne(self, context, **kw):
        from pyramid_formish.zcml import FormsDirective
        return FormsDirective(context, **kw)

    def test_after_render_view(self):
        from pyramid.view import render_view_to_response
        from pyramid.config import PyramidConfigurationMachine
        from pyramid.response import Response
        def view(context, request):
            return Response('response')
        context = PyramidConfigurationMachine()
        context.registry = self.config.registry
        context.autocommit = True
        directive = self._makeOne(context, view=view)
        directive.forms = [DummyFormDirective()]
        directive.actions = []
        directive.after()
        request = testing.DummyRequest()
        display = render_view_to_response(None, request, '')
        self.assertEqual(display.body, 'response')
        self.assertEqual(len(request.forms), 1)

    def test_after_render_controller_submission(self):
        from pyramid.view import render_view_to_response
        from pyramid.config import PyramidConfigurationMachine
        
        context = PyramidConfigurationMachine()
        context.registry = self.config.registry
        context.autocommit = True
        directive = self._makeOne(context, view=None)
        directive.forms = [DummyFormDirective()]
        directive.actions = []
        directive.after()
        request = testing.DummyRequest()
        request.params = {'__formish_form__':'form_id', 'submit':True}
        display = render_view_to_response(None, request, '')
        self.assertEqual(display.body, 'submitted')
        self.assertEqual(len(request.forms), 1)

    def test_after_render_controller_curriedview(self):
        from pyramid.view import render_view_to_response
        from pyramid.config import PyramidConfigurationMachine
        from pyramid_formish import ValidationError
        from pyramid.response import Response
        def view(context, request):
            return Response('response')
        context = PyramidConfigurationMachine()
        context.autocommit = True
        context.registry = self.config.registry
        directive = self._makeOne(context, view=view)
        formdirective = DummyFormDirective()
        formdirective.controller = make_controller_factory(
            exception=ValidationError)
        directive.forms = [formdirective]
        directive.actions = []
        directive.after()
        request = testing.DummyRequest()
        request.params = {'__formish_form__':'form_id', 'submit':True}
        display = render_view_to_response(None, request, '')
        self.assertEqual(display.body, 'response')
        self.assertEqual(len(request.forms), 1)

class FormDirectiveTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _makeOne(self, context, controller_factory, **kw):
        from pyramid_formish.zcml import FormDirective
        return FormDirective(context, controller_factory, **kw)

    def test_after_outside_forms_context(self):
        import webob.multidict
        import schemaish
        from pyramid.view import render_view_to_response
        from pyramid_formish.zcml import FormAction
        from pyramid.config import PyramidConfigurationMachine
        context = PyramidConfigurationMachine()
        context.autocommit = True
        context.registry = self.config.registry
        request = testing.DummyRequest()
        request.registry = self.config.registry
        title = schemaish.String()
        factory = make_controller_factory(fields=[('title', title)])
        directive = self._makeOne(context, factory)
        directive._actions = [FormAction('submit','title',True)]
        directive.after()
        display = render_view_to_response(None, request, '')
        self.assertEqual(display.body, '123')

        request = testing.DummyRequest()
        request.params = webob.multidict.MultiDict()
        request.params['submit'] = True
        display = render_view_to_response(None, request, '')
        self.assertEqual(display.body, 'submitted')

    def test_after_in_forms_context(self):
        context = DummyZCMLContext()
        context.forms = []
        directive = self._makeOne(context, None)
        directive.after()
        self.assertEqual(context.forms[0], directive)

    def test_bad_method(self):
        from zope.configuration.exceptions import ConfigurationError
        context = DummyZCMLContext()
        context.forms = []
        self.assertRaises(ConfigurationError,
                          self._makeOne, context, None, method='GOO')

    def test_good_method(self):
        context = DummyZCMLContext()
        context.forms = []
        inst = self._makeOne(context, None, method='GET')
        self.assertEqual(inst.method, 'GET')
        

class ActionDirectiveTests(unittest.TestCase):
    def setUp(self):
        testing.cleanUp()

    def tearDown(self):
        testing.cleanUp()

    def _callFUT(self, context, name, title=None, validate=True):
        from pyramid_formish.zcml import action
        return action(context, name, title, validate)

    def test_with_title(self):
        context = DummyZCMLContext()
        context.context = DummyZCMLContext()
        actions = context.context._actions = []
        self._callFUT(context, 'name', title='title', validate=False)
        self.assertEqual(len(actions), 1)
        action = actions[0]
        self.assertEqual(action.validate, False)
        self.assertEqual(action.name, 'name')
        self.assertEqual(action.title, 'title')
    
    def test_without_title(self):
        context = DummyZCMLContext()
        context.context = DummyZCMLContext()
        actions = context.context._actions = []
        self._callFUT(context, 'name', validate=False)
        self.assertEqual(len(actions), 1)
        action = actions[0]
        self.assertEqual(action.validate, False)
        self.assertEqual(action.name, 'name')
        self.assertEqual(action.title, 'Name')
    
class TestFormView(unittest.TestCase):
    def _makeOne(self, controller_factory, action, actions, form_id=None,
                 method='POST'):
        from pyramid_formish.zcml import FormView
        return FormView(controller_factory, action, actions, form_id=form_id,
                        method=method)

    def test_noname(self):
        import schemaish
        import validatish
        title = schemaish.String(validator=validatish.validator.Required())
        from pyramid_formish.zcml import FormAction
        action = FormAction(None, 'cancel', False)
        actions = [action]
        factory = make_controller_factory(fields=[('title', title)])
        view = self._makeOne(factory, action, actions)
        context = testing.DummyModel()
        request = testing.DummyRequest()
        result = view(context, request)
        self.assertEqual(result.body, '123')

    def test_formid(self):
        view = self._makeOne(None, {'name':1, 'validate':True}, None, 'default')
        self.assertEqual(view.form_id, 'default')

    def test_method(self):
        view = self._makeOne(None, None, None, 'default', method='GET')
        self.assertEqual(view.method, 'GET')

    def test_novalidate(self):
        import schemaish
        import validatish
        from pyramid_formish.zcml import FormAction
        title = schemaish.String(validator=validatish.validator.Required())
        action = FormAction('cancel', 'cancel', False)
        actions = [action]
        factory = make_controller_factory(fields=[('title', title)])
        view = self._makeOne(factory, action, actions)
        context = testing.DummyModel()
        request = testing.DummyRequest()
        result = view(context, request)
        self.assertEqual(result.body, 'cancelled')

    def test_with_actionsuccess(self):
        import schemaish
        from pyramid_formish.zcml import FormAction
        title = schemaish.String()
        L = []
        def success(controller, converted):
            L.append(converted)
            return 'success'
        action = FormAction('submit', 'submit', True, success)
        actions = [action]
        factory = make_controller_factory(fields=[('title', title)],
                                          defaults={'title':'the title'})
        view = self._makeOne(factory, action, actions)
        context = testing.DummyModel()
        request = testing.DummyRequest()
        result = view(context, request)
        self.assertEqual(result, 'success')
        self.assertEqual(L, [{'title':None}])

    def test_validate_no_error(self):
        import schemaish
        from pyramid_formish.zcml import FormAction
        title = schemaish.String()
        action = FormAction('submit', 'submit', True)
        actions = [action]
        factory = make_controller_factory(fields=[('title', title)],
                                          defaults={'title':'the title'})
        view = self._makeOne(factory, action, actions)
        context = testing.DummyModel()
        request = testing.DummyRequest()
        result = view(context, request)
        self.assertEqual(result.body, 'submitted')
        self.failUnless(request.form)
        self.assertEqual(dict(request.form.defaults), {'title':'the title'})

    def test_validate_form_error(self):
        import schemaish
        import validatish
        from pyramid_formish.zcml import FormAction
        title = schemaish.String(validator=validatish.validator.Required())
        action = FormAction('submit', 'submit', True)
        actions = [action]
        factory = make_controller_factory(fields=[('title', title)],
                                          defaults={'title':'the title'})
        view = self._makeOne(factory, action, actions)
        context = testing.DummyModel()
        request = testing.DummyRequest()
        result = view(context, request)
        self.assertEqual(result.body, '123')
        self.failUnless(request.form)
        self.assertEqual(dict(request.form.defaults), {'title':'the title'})
        self.failUnless('title' in request.form.errors)

    def test_validate_validation_error(self):
        import schemaish
        from pyramid_formish import ValidationError
        from pyramid_formish.zcml import FormAction
        title = schemaish.String()
        action = FormAction('submit', 'submit', True)
        actions = [action]
        factory = make_controller_factory(fields=[('title', title)],
                                          exception=ValidationError(title='a'),
                                          defaults={'title':'the title'})
        view = self._makeOne(factory, action, actions)
        context = testing.DummyModel()
        request = testing.DummyRequest()
        result = view(context, request)
        self.assertEqual(result.body, '123')
        self.failUnless(request.form)
        self.assertEqual(dict(request.form.defaults), {'title':'the title'})
        self.failUnless('title' in request.form.errors)

    def test_selfvalidate(self):
        import schemaish
        import validatish
        from pyramid_formish.zcml import FormAction
        title = schemaish.String()
        action = FormAction('submit', 'submit', True)
        actions = [action]
        title = schemaish.String(validator=validatish.validator.Required())
        factory = make_controller_factory(selfvalidate=True,
                                          fields=[('title', title)])
        view = self._makeOne(factory, action, actions)
        context = testing.DummyModel()
        request = testing.DummyRequest()
        result = view(context, request)
        self.assertEqual(result.body, 'validated')

    def test_with_widgets(self):
        import schemaish
        import validatish
        import formish
        from pyramid_formish.zcml import FormAction
        action = FormAction(None, 'cancel', False)
        title = schemaish.String(validator=validatish.validator.Required())
        actions = [action]
        titlewidget = formish.Input()
        factory = make_controller_factory(fields=[('title', title)],
                                          widgets={'title':titlewidget})
        view = self._makeOne(factory, action, actions)
        context = testing.DummyModel()
        request = testing.DummyRequest()
        result = view(context, request)
        self.assertEqual(result.body, '123')

    def test_with_method_GET(self):
        import schemaish
        import validatish
        import formish
        from pyramid_formish.zcml import FormAction
        action = FormAction(None, 'cancel', False)
        title = schemaish.String(validator=validatish.validator.Required())
        actions = [action]
        titlewidget = formish.Input()
        factory = make_controller_factory(fields=[('title', title)],
                                          widgets={'title':titlewidget})
        view = self._makeOne(factory, action, actions, method='GET')
        context = testing.DummyModel()
        request = testing.DummyRequest()
        result = view(context, request)
        self.assertEqual(result.body, '123')

class TestAddTemplatePath(unittest.TestCase):
    def tearDown(self):
        testing.cleanUp()
        
    def _callFUT(self, context, path):
        from pyramid_formish.zcml import add_template_path
        return add_template_path(context, path)

    def test_abspath(self):
        from pyramid_formish.zcml import IFormishSearchPath
        from zope.component import getUtility
        import os.path
        here = os.path.dirname(__file__)
        abspath = os.path.abspath(here)
        context = DummyZCMLContext()
        self._callFUT(context, abspath)
        context.ac[0]['callable']()
        self.assertEqual(getUtility(IFormishSearchPath), [abspath])

    def test_pkg_relpath(self):
        from pyramid_formish.zcml import IFormishSearchPath
        import pyramid_formish.tests
        from zope.component import getUtility
        import os.path
        context = DummyZCMLContext(pyramid_formish.tests)
        self._callFUT(context, 'fixtures')
        context.ac[0]['callable']()
        here = os.path.dirname(__file__)
        abspath = os.path.abspath(here)
        self.assertEqual(getUtility(IFormishSearchPath),
                         [os.path.join(abspath, 'fixtures')]
                          )

    def test_pkg_abspath(self):
        from pyramid_formish.zcml import IFormishSearchPath
        import pyramid_formish.tests
        from zope.component import getUtility
        import os.path
        context = DummyZCMLContext(pyramid_formish.tests)
        self._callFUT(context, 'chameleon.formish.tests:fixtures')
        context.ac[0]['callable']()
        here = os.path.dirname(__file__)
        abspath = os.path.abspath(here)
        self.assertEqual(getUtility(IFormishSearchPath),
                         [os.path.join(abspath, 'fixtures')]
                          )
        
        
class DummyZCMLContext:
    info = None
    package = 'pyramid_formish'
    registry = None
    autocommit = True
    def __init__(self, resolved=None):
        self.resolved = resolved
        self.ac =[]
    def action(self, **kw):
        self.ac.append(kw)
    def resolve(self, package_name):
        return self.resolved

def make_controller_factory(fields=(), defaults=None, result='123',
                            widgets=None, selfvalidate=False, exception=None):
    from pyramid.response import Response
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
            return Response(result)
        def form_defaults(self):
            if defaults is None:
                return {}
            return defaults
        def handle_submit(self, converted):
            if exception:
                raise exception
            return Response('submitted')
        def handle_cancel(self):
            return Response('cancelled')
        if selfvalidate:
            def validate(self):
                return Response('validated')

    return DummyController

class DummyFormDirective(object):
    def __init__(self):
        self.form_id = 'form_id'
        self._actions = [DummyAction()]
        self.controller = make_controller_factory()

class DummyAction(object):
    name = 'submit'
    title = 'Submit'
    validate = True
    success = False
    
    
    
