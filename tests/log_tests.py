from dataikuapi.dssclient import DSSClient
from nose.tools import ok_
from nose.tools import eq_

host="http://localhost:8082"
apiKey="ZZYqWxPnc2nWMJMUXwykn6wzA7jokbp5"

def list_logs_test():
	client = DSSClient(host, apiKey)
	ok_(len(client.list_logs()) > 0)

def get_log_test():
	client = DSSClient(host, apiKey)
	log = client.get_log('error.log')
	ok_(log is not None)


