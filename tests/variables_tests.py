from dataikuapi.dssclient import DSSClient

host="http://localhost:8082"
apiKey="ZZYqWxPnc2nWMJMUXwykn6wzA7jokbp5"

def get_variables_test():
	client = DSSClient(host, apiKey)
	print(client.get_variables())

def set_variables_test():
	client = DSSClient(host, apiKey)
	vars = client.get_variables()
	vars['a'] = 'b'
	client.set_variables(vars)
	print(client.get_variables())

