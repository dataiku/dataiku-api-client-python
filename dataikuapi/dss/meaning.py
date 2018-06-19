
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

        :returns: the meaning definition, as a dict. The precise structure of the dict depends on the meaning type and is not documented.
        """
        return self.client._perform_json(
            "GET", "/meanings/%s" % self.id)

    def set_definition(self, definition):
        """
        Set the meaning's definition.

        Note: this call requires an API key with admin rights

        :param dict definition: the definition for the meaning, as a dict. You should only ``set_definition`` on a modified version of a dict you retrieved via :py:meth:`get_definition`
        """
        return self.client._perform_json(
            "PUT", "/meanings/%s" % self.id,
            body = definition)

