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

	def t01_render_and_wait_and_download(self):
		webapps = self.project.list_webapps();

		ok_(len(webapps) > 0)
