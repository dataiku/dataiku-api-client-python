from dataikuapi.dssclient import DSSClient
from nose.tools import ok_
from nose.tools import eq_

host="http://localhost:8082"
apiKey="ZZYqWxPnc2nWMJMUXwykn6wzA7jokbp5"


def list_users_test():
	client = DSSClient(host, apiKey)
	users = client.list_users()
	ok_(len(users) > 0)

def create_delete_user_test():
	client = DSSClient(host, apiKey)
	count = len(client.list_users())	
	
	user = client.create_user("toto", "password", "display name of toto", groups=['a','b'])
	eq_(count + 1, len(client.list_users()))
	
	user.delete()
	eq_(count, len(client.list_users()))
	
def get_set_user_test():
	client = DSSClient(host, apiKey)
	user = client.create_user("toto", "password", "display name of toto", groups=['a','b'])
	
	desc = user.get_definition()
	desc['displayName'] = 'tata'
	user.set_definition(desc)
	desc2 = user.get_definition()
	
	eq_('tata', desc2['displayName'])

	user.delete()
	
