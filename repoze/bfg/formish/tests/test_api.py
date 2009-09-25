import unittest
from repoze.bfg import testing

class TestTemplateLoader(unittest.TestCase):
    def _makeOne(self, **kw):
        from repoze.bfg.formish import TemplateLoader
        return TemplateLoader(**kw)

    def test_search_path_None(self):
        loader = self._makeOne()
        self.assertEqual(loader.search_path, [])

    def test_search_path_string(self):
        loader = self._makeOne(search_path='path')
        self.assertEqual(loader.search_path, ['path'])

    def test_load_exists(self):
        import os
        fixtures = os.path.join(os.path.dirname(__file__), 'fixtures')
        loader = self._makeOne(search_path=[fixtures])
        result = loader.load('test.html')
        self.failUnless(result)

    def test_load_notexists(self):
        import os
        import mako
        fixtures = os.path.join(os.path.dirname(__file__), 'fixtures')
        loader = self._makeOne(search_path=[fixtures])
        self.assertRaises(mako.exceptions.TopLevelLookupException,
                          loader.load, 'doesnt.html')
        self.failUnless(
            os.path.join(fixtures, 'doesnt.html') in loader.notexists)

    def test_load_negative_cache(self):
        import os
        fixtures = os.path.join(os.path.dirname(__file__), 'fixtures')
        path = os.path.join(fixtures, 'test.html')
        loader = self._makeOne(search_path=[fixtures], auto_reload=True)
        loader.notexists[path] = True
        result = loader.load('test.html')
        self.failUnless(result)

    def test_load_negative_cache2(self):
        import os
        import mako
        fixtures = os.path.join(os.path.dirname(__file__), 'fixtures')
        path = os.path.join(fixtures, 'test.html')
        loader = self._makeOne(search_path=[fixtures], auto_reload=False)
        loader.notexists[path] = True
        self.assertRaises(mako.exceptions.TopLevelLookupException,
                          loader.load, 'test.html')

class TestZPTRenderer(unittest.TestCase):
    def tearDown(self):
        testing.cleanUp()

    def _getTargetClass(self):
        from repoze.bfg.formish import ZPTRenderer
        return ZPTRenderer
    
    def _makeOne(self, *arg, **kw):
        return self._getTargetClass()(*arg, **kw)

    def test_ctor_nodirs(self):
        renderer = self._makeOne()
        self.assertEqual(renderer.directories, [])

    def test_ctor_stringdir(self):
        renderer = self._makeOne(directories='tests')
        self.assertEqual(renderer.directories, ['tests'])

    def test_call_defaultdir(self):
        renderer = self._makeOne()
        result = renderer('formish/test/test.html', {})
        self.assertEqual(result, u'<div>Test</div>')

    def test_call_template_startswith_slash(self):
        renderer = self._makeOne()
        result = renderer('/formish/test/test.html', {})
        self.assertEqual(result, u'<div>Test</div>')


    def test_call_extradir(self):
        from pkg_resources import resource_filename
        renderer = self._makeOne(
            [resource_filename('repoze.bfg.formish.tests', 'fixtures')])
        result = renderer('test.html', {})
        self.assertEqual(result, u'<div>Fixtures</div>')
        
    def test_call_with_utility_registrations(self):
        from pkg_resources import resource_filename
        from zope.component import getSiteManager
        from repoze.bfg.formish import IFormishSearchPath
        sm = getSiteManager()
        sm.registerUtility([resource_filename('repoze.bfg.formish.tests',
                                              'fixtures')],
                           IFormishSearchPath)
        renderer = self._makeOne(
            [])
        result = renderer('test.html', {})
        self.assertEqual(result, u'<div>Fixtures</div>')

class TestForm(unittest.TestCase):
    def _makeOne(self, *arg, **kw):
        from repoze.bfg.formish import Form
        return Form(*arg, **kw)

    def test_with_renderer(self):
        from schemaish import Structure
        from repoze.bfg.formish import ZPTRenderer
        form = self._makeOne(Structure(), renderer=None)
        self.failIfEqual(form.renderer.__class__, ZPTRenderer)
        
    def test_default_renderer(self):
        from schemaish import Structure
        from repoze.bfg.formish import ZPTRenderer
        form = self._makeOne(Structure())
        self.failUnlessEqual(form.renderer.__class__, ZPTRenderer)

    def test_set_widget(self):
        import schemaish
        from formish.widgets import Widget
        class DummySchema(schemaish.Structure):
            title = schemaish.String()
        form = self._makeOne(DummySchema())
        widget = Widget()
        form.set_widget('title', widget)
        self.assertEqual(form['title'].widget.widget, widget)
        
        
