import unittest
from repoze.bfg import testing

class TestZPTRenderer(unittest.TestCase):
    def tearDown(self):
        testing.cleanUp()

    def _getTargetClass(self):
        from repoze.bfg.formish import ZPTRenderer
        return ZPTRenderer
    
    def _makeOne(self, *arg, **kw):
        return self._getTargetClass()(*arg, **kw)

    def test_call_defaultdir(self):
        renderer = self._makeOne()
        result = renderer('formish/test/test.html', {})
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
