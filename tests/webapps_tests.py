from time import sleep
from dataikuapi.dssclient import DSSClient
from dataikuapi.dss.project import DSSProject
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

class webapp_api_tests(object):

	def setUp(self):
		self.client = DSSClient(host, apiKey)
		self.project = DSSProject(self.client, testProjectKey)

	def list_webapps_test(self):
		webapps = self.project.list_webapps();
		ok_(len(webapps) > 0)


	def get_python_webapp_test(self):
		webapp = self.project.get_webapp(testWebAppPythonId)
		ok_(webapp is not None)

	def update_python_webapp_test(self):
		webapp_pre = self.project.get_webapp(testWebAppPythonId)
		webapp_pre.update()
		webapp_post = self.project.get_webapp(testWebAppPythonId)
		eq_(webapp_pre.project_key, webapp_post.project_key)
		eq_(webapp_pre.webapp_id, webapp_post.webapp_id)
		eq_(remove_key(webapp_pre.definition, "versionTag"), remove_key(webapp_post.definition, "versionTag"))
		eq_(webapp_pre.definition["versionTag"]["versionNumber"]+1,webapp_post.definition["versionTag"]["versionNumber"])

	def restart_backend_test(self):
		"""
		WARNING: you should manually stop the backend before this test
		"""
		filtered_webapps = [w for w in self.project.list_webapps() if w.webapp_id == testWebAppPythonId]
		webapp = self.project.get_webapp(testWebAppPythonId)
		ok_(not filtered_webapps[0].definition["backendRunning"],"The backend should be stopped before the test")
		webapp.restart_backend()
		sleep(2)
		filtered_webapps = [w for w in self.project.list_webapps() if w.webapp_id == testWebAppPythonId]
		ok_(filtered_webapps[0].definition["backendRunning"])

	def stop_backend_test(self):
		"""
		WARNING: you should manually start the backend before this test
		"""
		filtered_webapps = [w for w in self.project.list_webapps() if w.webapp_id == testWebAppPythonId]
		webapp = self.project.get_webapp(testWebAppPythonId)
		ok_(filtered_webapps[0].definition["backendRunning"],"The backend should be started before the test")
		webapp.stop_backend()
		sleep(2)
		filtered_webapps = [w for w in self.project.list_webapps() if w.webapp_id == testWebAppPythonId]
		ok_(not filtered_webapps[0].definition["backendRunning"])