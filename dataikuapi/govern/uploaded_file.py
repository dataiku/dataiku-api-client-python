class GovernUploadedFile(object):
    """
    A handle to interact with an uploaded file
    Do not create this directly, use :meth:`~dataikuapi.GovernClient.get_uploaded_file`
    """

    def __init__(self, client, uploaded_file_id):
        self.client = client
        self.uploaded_file_id = uploaded_file_id

    def get_description(self):
        """
        Get the description of the uploaded file.

        :return: The description of the file as a python dict
        :rtype: dict
        """

        return self.client._perform_json("GET", "/uploaded-file/%s" % self.uploaded_file_id)

    def delete(self):
        """
        Delete the file

        :return: None
        """

        return self.client._perform_empty("DELETE", "/uploaded-files/%s" % self.uploaded_file_id)
