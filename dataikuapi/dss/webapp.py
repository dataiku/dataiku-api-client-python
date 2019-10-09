import sys

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
    def __init__(self, client, project_key, webapp_id, definition):
        """Do not call directly, use :meth:`dataikuapi.dss.project.DSSProject.get_webapps`"""
        self.client = client
        self.project_key = project_key
        self.webapp_id = webapp_id
        self.definition = definition

    """
    Update an existing webapp

    :returns: a webapp state excerpt
    :rtype: :class:`dataikuapi.dss.webapp.DSSWebAppSaveResponse`
    """
    def update(self):
        response =  self.client._perform_json("PUT", "/projects/%s/webapps/%s" % (self.project_key, self.webapp_id), body=self.definition)
        return DSSWebAppSaveResponse(self.client, self.project_key, self.webapp_id, response)

    """
    Stop a webapp
    """
    def stop_backend(self):
        self.client._perform_json("PUT", "/projects/%s/webapps/%s/stop-backend" % (self.project_key, self.webapp_id))
        return

    """
    Restart a webapp
    """
    def restart_backend(self):
        self.client._perform_json("PUT", "/projects/%s/webapps/%s/restart-backend" % (self.project_key, self.webapp_id))
        return


class DSSWebAppSaveResponse(object):
    """
    Response for the update method on a WebApp
    """
    def __init__(self, client, project_key, webapp_id, definition):
        """Do not call directly, use :meth:`dataikuapi.dss.webapp.DSSWebApp.update`"""
        self.client = client
        self.project_key = project_key
        self.webapp_id = webapp_id
        self.definition = definition


class DSSWebAppHead(object):
    """
    A handle to manage a webapp head
    """
    def __init__(self, client, project_key, webapp_id, definition):
        """Do not call directly, use :meth:`dataikuapi.dss.project.DSSProject.get_webapps`"""
        self.client = client
        self.project_key = project_key
        self.webapp_id = webapp_id
        self.definition = definition
