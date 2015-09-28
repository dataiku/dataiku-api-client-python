from dataikuapi.dssclient import DSSClient
from nose.tools import ok_
from nose.tools import eq_

host="http://localhost:8082"
apiKey="ZZYqWxPnc2nWMJMUXwykn6wzA7jokbp5"

def list_connections_test():
	client = DSSClient(host, apiKey)
	connections = client.list_connections()
	ok_(len(connections) > 0)	

def create_delete_connection_test():
	client = DSSClient(host, apiKey)
	count = len(client.list_connections())	
	
	connection = client.create_connection("toto", "HDFS")
	eq_(count + 1, len(client.list_connections()))	
	
	connection.delete()
	eq_(count, len(client.list_connections()))	
	
def get_set_connection_test():
	client = DSSClient(host, apiKey)
	connection = client.create_connection("toto", "HDFS")
	
	desc = connection.get_definition()
	desc['usableBy'] = 'ALLOWED'
	desc['allowedGroups'] = ['a','b']
	connection.set_definition(desc)

	desc2 = connection.get_definition()
	eq_('ALLOWED', desc2['usableBy'])	
	
	connection.delete()
	
