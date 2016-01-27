
class DSSMeaning(object):
    """
    A user-defined meaning on the DSS instance
    """
    def __init__(self, client, id):
        self.client = client
        self.id = id

    ########################################################
    # Meaning definition
    ########################################################

    def get_definition(self):
        """
        Get the meaning's definition.

        Note: this call requires an API key with admin rights

        Returns:
            the meaning definition, as a JSON object
        """
        return self.client._perform_json(
            "GET", "/meanings/%s" % self.id)

    def set_definition(self, definition):
        """
        Set the meaning's definition.

        Note: this call requires an API key with admin rights

        Args:
            definition: the definition for the meaning, as a JSON object
        """
        return self.client._perform_json(
            "PUT", "/meanings/%s" % self.id,
            body = definition)

