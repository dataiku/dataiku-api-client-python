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

	def list_webapps_test(self):
		webapps = self.project.list_webapps();
		ok_(len(webapps) > 0)

	def get_python_webapp_test(self):
		webapp = self.project.get_webapp(testWebAppPythonId)
		ok_(webapp is not None)

	def get_definition_test(self):
		webapp = self.project.get_webapp(testWebAppPythonId)
		definition = webapp.get_definition()
		ok_(definition is not None)
		eq_(definition.webapp_id, testWebAppPythonId)
		eq_(definition.get_definition()["id"], testWebAppPythonId)

	def update_python_webapp_test(self):
		webapp = self.project.get_webapp(testWebAppPythonId)
		definition = webapp.get_definition()
		old_def = dict(definition.get_definition())
		future = definition.save()
		ok_(future is not None)
		eq_(remove_key(definition.get_definition(), "versionTag"), remove_key(old_def, "versionTag"))
		eq_(definition.get_definition()["versionTag"]["versionNumber"], old_def["versionTag"]["versionNumber"] + 1)

	def restart_backend_test(self):
		"""
		WARNING: you should manually stop the backend before this test
		"""
		filtered_webapps = [w for w in self.project.list_webapps() if w.webapp_id == testWebAppPythonId]
		ok_(not filtered_webapps[0].get_state()["backendRunning"], "The backend should be stopped before the test")
		future = filtered_webapps[0].restart_backend()
		future.wait_for_result()
		filtered_webapps = [w for w in self.project.list_webapps() if w.webapp_id == testWebAppPythonId]
		ok_(filtered_webapps[0].get_state()["backendRunning"])

	def stop_backend_test(self):
		"""
		WARNING: you should manually start the backend before this test
		"""
		filtered_webapps = [w for w in self.project.list_webapps() if w.webapp_id == testWebAppPythonId]
		ok_(filtered_webapps[0].get_state()["backendRunning"],"The backend should be started before the test")
		filtered_webapps[0].stop_backend()
		sleep(2)
		filtered_webapps = [w for w in self.project.list_webapps() if w.webapp_id == testWebAppPythonId]
		ok_(not filtered_webapps[0].get_state()["backendRunning"])