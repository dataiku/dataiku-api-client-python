from dataikuapi.dssclient import DSSClient
from nose.tools import ok_
from nose.tools import eq_

host="http://localhost:8082"
apiKey="ZZYqWxPnc2nWMJMUXwykn6wzA7jokbp5"

def list_groups_test():
	client = DSSClient(host, apiKey)
	groups = client.list_groups()
	ok_(len(groups) > 0)

def create_delete_group_test():
	client = DSSClient(host, apiKey)
	count = len(client.list_groups())	
	
	group = client.create_group("toto")
	eq_(count + 1, len(client.list_groups()))
	
	group.delete()
	eq_(count, len(client.list_groups()))
	
def get_set_group_test():
	client = DSSClient(host, apiKey)
	group = client.create_group("toto")
	
	desc = group.get_definition()
	desc['description'] = 'here'
	group.set_definition(desc)
	desc2 = group.get_definition()
	
	eq_('here', desc2['description'])

	group.delete()
	
