

class DSSDataset(object):

	def __init__(self, client, project_key, dataset_name):
		self.client = client
		self.project_key = project_key
		self.dataset_name = dataset_name

	def get_schema(self):
		return self.client._perform_json(
				"GET", "/projects/%s/datasets/%s/schema" % (self.project_key, self.dataset_name))

	def set_schema(self, schema):
		return self.client._perform_json(
				"PUT", "/projects/%s/datasets/%s/schema" % (self.project_key, self.dataset_name),
				body=schema)