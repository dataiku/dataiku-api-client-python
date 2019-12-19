from time import sleep
from dataikuapi.dssclient import DSSClient
from dataikuapi.dss.project import DSSProject
from dataikuapi.dss.ml import DSSMLTask
from nose.tools import ok_
from nose.tools import eq_

host="http://localhost:8083"
apiKey="pn2bwlgjpy0IhUYzGz2ECEE6EzhqF2kE"
testProjectKey="TITANICTAMER"
analysis="JIGnQdJW"
mlTaskId="vjcQiaA8"


def remove_key(d, key):
	r = dict(d)
	del r[key]
	return r


class ML_tests(object):

	def __init__(self):
		self.client = None
		self.project = None;

	def setUp(self):
		self.client = DSSClient(host, apiKey)
		self.project = DSSProject(self.client, testProjectKey)

	def t01_list_webapps_test(self):
		task = DSSMLTask(self.client, self.project.project_key, analysis, mlTaskId)
		future  = task.start_render("A-TITANICTAMER-JIGnQdJW-vjcQiaA8-s1-pp1-m1")
		ok_(future is not None)
		ok_(future.job_id is not None)
		filename = future.wait_for_result()
		ok_(filename is not None and len(filename)>0)
		rendered = task.render_download(filename)
		ok_(rendered is not None)
