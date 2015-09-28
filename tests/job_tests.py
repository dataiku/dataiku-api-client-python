from dataikuapi.dssclient import DSSClient
from nose.tools import ok_
from nose.tools import eq_

host="http://localhost:8082"
apiKey="ZZYqWxPnc2nWMJMUXwykn6wzA7jokbp5"
testProjectKey="IMPALA"
testDataset="cat_train_hdfs"

def list_jobs_test():
	client = DSSClient(host, apiKey)
	jobs = client.get_project(testProjectKey).list_jobs()
	ok_(len(jobs) > 0)

def job_status_test():
	client = DSSClient(host, apiKey)
	project = client.get_project(testProjectKey)
	jobs = project.list_jobs()
	for job in jobs:
		status = project.get_job(job['def']['id']).get_status()
		ok_(status is not None)
		
def job_log_test():
	client = DSSClient(host, apiKey)
	project = client.get_project(testProjectKey)
	jobs = project.list_jobs()
	for job in jobs:
		log = project.get_job(job['def']['id']).get_log()
		ok_(log is not None)


def job_start_abort_test():
	client = DSSClient(host, apiKey)
	project = client.get_project(testProjectKey)
	
	count = len(client.get_project(testProjectKey).list_jobs())
	
	job = project.start_job({
		"initiator" : "me",
		"name" : "some job",
		"triggeredFrom" : "API",
		"type" : "NON_RECURSIVE_FORCED_BUILD",
		"outputs" : [{
						"type" : "DATASET",
						"projectKey" : testProjectKey,
						"id" : testDataset,
						"partition" : "NP"
					}]
	})
	job.abort()

	eq_(count + 1, len(client.get_project(testProjectKey).list_jobs()))

