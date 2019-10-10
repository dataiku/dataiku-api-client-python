import sys
from .future import DSSFuture

if sys.version_info >= (3,0):
  import urllib.parse
  dku_quote_fn = urllib.parse.quote
else:
  import urllib
  dku_quote_fn = urllib.quote


class DSSWebApp(object):
    """
    A handle to manage a webapp
    """
    def __init__(self, client, project_key, webapp_id, state=None):
        """Do not call directly, use :meth:`dataikuapi.dss.project.DSSProject.get_webapps`"""
        self.client = client
        self.project_key = project_key
        self.webapp_id = webapp_id
        self.state = state

    def get_state(self):
        """
        Return the state of the webapp

        :return: the state of the webapp
        """
        if self.state is None:
            webapps = self.client._perform_json("GET", "/projects/%s/webapps/" % self.project_key)

            filtered_webapps = [w for w in webapps if w["id"] == self.webapp_id]
            if len(filtered_webapps) > 0:
                self.state = filtered_webapps[0]
        return self.state

    def stop_backend(self):
        """
        Stop a webapp
        """
        self.client._perform_empty("PUT", "/projects/%s/webapps/%s/stop-backend" % (self.project_key, self.webapp_id))
        self.state = None
        return

    def restart_backend(self):
        """
        Restart a webapp
        """
        future = self.client._perform_json("PUT", "/projects/%s/webapps/%s/restart-backend" % (self.project_key, self.webapp_id))
        self.state = None
        return DSSFuture(self.client, future["jobId"])

    def get_definition(self):
        """
        Get a webapp definition
        :returns: a handle to manage the webapp definition
        :rtype: :class:`dataikuapi.dss.webapp.DSSWebAppDefinition`
        """
        definition = self.client._perform_json("GET", "/projects/%s/webapps/%s" % (self.project_key, self.webapp_id))
        return DSSWebAppDefinition(self.client, self.project_key, self.webapp_id, definition)


class DSSWebAppDefinition(object):
    """
    A handle to manage a WebApp definition
    """
    def __init__(self, client, project_key, webapp_id, definition):
        """Do not call directly, use :meth:`dataikuapi.dss.webapp.DSSWebApp.get_definition`"""
        self.client = client
        self.project_key = project_key
        self.webapp_id = webapp_id
        self.definition = definition

    def get_definition(self):
        """
        Get the definition


        :returns: the definition of the webapp
        """
        return self.definition

    def set_definition(self, definition):
        """
        Set the definition

        :param definition : the definition of the webapp
        """
        self.definition = definition

    def save(self):
        """
        Save the current webapp definition and update
        :returns: a wrapper to a future
        """
        future = self.client._perform_json("PUT", "/projects/%s/webapps/%s" % (self.project_key, self.webapp_id), body=self.definition)
        self.definition = self.client._perform_json("GET", "/projects/%s/webapps/%s" % (self.project_key, self.webapp_id))
        return future
