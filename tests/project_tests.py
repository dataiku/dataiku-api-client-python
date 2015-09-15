from dataikuapi.dssclient import DSSClient
from nose.tools import ok_
from nose.tools import eq_

host="http://localhost:8082"
apiKey="aa"
testProjectKey="IO_HARMO"


def list_projects_test():
	client = DSSClient(host, apiKey)
	projects = client.list_projects()
	ok_(len(projects) > 0)
	
def project_metadata_test():
	client = DSSClient(host, apiKey)
	project = client.get_project(testProjectKey)
	meta = project.get_metadata()
	ok_(meta is not None)
	project.set_metadata(meta)
		
def project_permissions_test():
	client = DSSClient(host, apiKey)
	project = client.get_project(testProjectKey)
	perms = project.get_permissions()
	ok_(perms is not None)
	project.set_permissions(perms)
	
def project_create_delete_test():
	client = DSSClient(host, apiKey)
	count = len(client.list_projects())

	p = client.create_project("toto","name of toto", "me")
	eq_(count + 1, len(client.list_projects()))
	
	p.delete()
	eq_(count, len(client.list_projects()))


"""
def sql_test():
	client = DSSClient(host, apiKey)
	projects = client.list_projects()
	projectKey = projects[0]['projectKey']
	p = client.get_project(projectKey)
	q = p.sql_query('select * from train_set_pg limit 5', 'local_postgress')
	for r in q.iter_rows():
		print(r)
	q.verify()


def project_export_stream_test():
	client = DSSClient(host, apiKey)
	with client.get_project('PARTITIONED').get_export_stream() as e:
		with open('export.zip', 'w') as f:
			f.write(e.read())
			
def project_export_file_test():
	client = DSSClient(host, apiKey)
	client.get_project('PARTITIONED').export_to_file("ex2.zip")

"""

