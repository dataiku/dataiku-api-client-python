from time import sleep
from dataikuapi.dssclient import DSSClient
from dataikuapi.dss.project import DSSProject
from dataikuapi.dss.webapp import DSSWebApp
from nose.tools import ok_
from nose.tools import eq_

host="http://localhost:8083"
apiKey="CMZBjFkUgcDh08S3awoPyVIweBelxPjy"
testProjectKey="WEBAPPS"
testWebAppPythonId="VCMN2ra"


def remove_key(d, key):
	r = dict(d)
	del r[key]
	return r


class WebappApi_tests(object):

	def __init__(self):
		self.client = None
		self.project = None;

	def setUp(self):
		self.client = DSSClient(host, apiKey)
		self.project = DSSProject(self.client, testProjectKey)

	def t01_list_webapps_test(self):
		webapps = self.project.list_webapps();
		ok_(len(webapps) > 0)

	def t02_get_python_webapp_test(self):
		webapp = self.project.get_webapp(testWebAppPythonId)
		ok_(webapp is not None)

	def t03_get_definition_test(self):
		webapp = self.project.get_webapp(testWebAppPythonId)
		definition = webapp.get_definition()
		ok_(definition is not None)
		eq_(definition.webapp_id, testWebAppPythonId)
		eq_(definition.get_definition()["id"], testWebAppPythonId)

	def t04_update_python_webapp_test(self):
		webapp = self.project.get_webapp(testWebAppPythonId)
		definition = webapp.get_definition()
		old_def = dict(definition.get_definition())
		definition.save()
		eq_(remove_key(definition.get_definition(), "versionTag"), remove_key(old_def, "versionTag"))
		eq_(definition.get_definition()["versionTag"]["versionNumber"], old_def["versionTag"]["versionNumber"] + 1)

	def t05_restart_backend_test(self):
		"""
		WARNING: you should manually stop the backend before this test
		"""
		webapp = self.project.get_webapp(testWebAppPythonId)
		ok_(not webapp.get_state().is_running(), "The backend should be stopped before the test")
		future = webapp.restart_backend()
		future.wait_for_result()
		ok_(webapp.get_state().is_running())

	def t06_stop_backend_test(self):
		"""
		WARNING: you should manually start the backend before this test
		"""
		webapp = self.project.get_webapp(testWebAppPythonId)
		ok_(webapp.get_state().is_running(),"The backend should be started before the test")
		webapp.stop_backend()
		sleep(2)
		eq_(webapp.get_state().is_running(), False)

	def t07_state_consistency_test(self):
		webapp = self.project.get_webapp(testWebAppPythonId)
		webapp.stop_backend()
		eq_(webapp.get_state().is_running(), False)
		future = webapp.restart_backend()
		future.wait_for_result()
		eq_(webapp.get_state().is_running(), True)
		webapp.stop_backend()
		eq_(webapp.get_state().is_running(), False)