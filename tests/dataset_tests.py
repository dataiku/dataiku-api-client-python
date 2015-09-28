from dataikuapi.dssclient import DSSClient
import json
from nose.tools import ok_
from nose.tools import eq_

host="http://localhost:8082"
apiKey="ZZYqWxPnc2nWMJMUXwykn6wzA7jokbp5"
testProjectKey="IMPALA"
testDataset="tube"
testHiveDataset="cat_train_hdfs"
testPartitionedProjectKey="PARTITIONED"
testPartitionedDataset="rundec2"
testDropPartitionedDataset="rundec2"
testDropPartition="access"
testClearDataset = 'train_set_pg2'

def list_datasets_test():
	client = DSSClient(host, apiKey)
	datasets = client.get_project(testProjectKey).list_datasets()
	ok_(len(datasets) > 0)	

def dataset_data_test():
	client = DSSClient(host, apiKey)
	p = client.get_project(testProjectKey)
	d = p.get_dataset(testDataset)
	counter = 0
	for r in d.iter_rows():
		counter = counter + 1
		if counter > 5:
			break
	eq_(6, counter)
	# note : backend will get a pipe broken
	
def sync_metastore_test():
	client = DSSClient(host, apiKey)
	dataset = client.get_project(testProjectKey).get_dataset(testHiveDataset)
	dataset.synchronize_hive_metastore()
	# didn't die


def clear_test():
	client = DSSClient(host, apiKey)
	dataset = client.get_project(testProjectKey).get_dataset(testClearDataset)
	dataset.clear()


def list_partitions_test():
	client = DSSClient(host, apiKey)
	dataset = client.get_project(testPartitionedProjectKey).get_dataset(testPartitionedDataset)
	ok_(len(dataset.list_partitions()) > 0)

def clear_partitions_test():
	client = DSSClient(host, apiKey)
	dataset = client.get_project(testPartitionedProjectKey).get_dataset(testDropPartitionedDataset)
	dataset.clear(json.dumps([testDropPartition]))

def create_delete_test():
	client = DSSClient(host, apiKey)
	project = client.get_project(testProjectKey)
	count = len(project.list_datasets())

	dataset = project.create_dataset("titi", "Filesystem")
	eq_(count + 1, len(project.list_datasets()))
	
	dataset.delete()	
	eq_(count, len(project.list_datasets()))
	
	
def get_set_test():
	client = DSSClient(host, apiKey)
	project = client.get_project(testProjectKey)
	dataset = project.create_dataset("titi", "Filesystem")
	
	definition = dataset.get_definition()
	definition['managed'] = True
	dataset.set_definition(definition)
	definition2 = dataset.get_definition()

	eq_(True, definition2['managed'])
	
	dataset.delete()	
