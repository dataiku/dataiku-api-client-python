from ..utils import DataikuException
from .future import DSSFuture
import json, warnings
from .utils import DSSTaggableObjectListItem
from .future import DSSFuture
from .discussion import DSSObjectDiscussions
from . import recipe

try:
    basestring
except NameError:
    basestring = str

class DSSStreamingEndpointListItem(DSSTaggableObjectListItem):
    """An item in a list of streaming endpoints. Do not instantiate this class"""
    def __init__(self, client, data):
        super(DSSStreamingEndpointListItem, self).__init__(data)
        self.client = client

    def to_streaming_endpoint(self):
        """Gets the :class:`DSSStreamingEndpoint` corresponding to this streaming endpoint"""
        return DSSStreamingEndpoint(self.client, self._data["projectKey"], self._data["id"])

    @property
    def name(self):
        return self._data["id"]
    @property
    def id(self):
        return self._data["id"]
    @property
    def type(self):
        return self._data["type"]
    @property
    def schema(self):
        return self._data["schema"]

    @property
    def connection(self):
        """Returns the connection on which this streaming endpoint is attached, or None if there is no connection for this streaming endpoint"""
        if not "params" in self._data:
            return None
        return self._data["params"].get("connection", None)

    def get_column(self, column):
        """
        Returns the schema column given a name.
        :param str column: Column to find
        :return a dict of the column settings or None if column does not exist
        """
        matched = [col for col in self.schema["columns"] if col["name"] == column]
        return None if len(matched) == 0 else matched[0]

class DSSStreamingEndpoint(object):
    """
    A streaming endpoint on the DSS instance
    """
    def __init__(self, client, project_key, streaming_endpoint_name):
        self.client = client
        self.project = client.get_project(project_key)
        self.project_key = project_key
        self.streaming_endpoint_name = streaming_endpoint_name

    ########################################################
    # Streaming Endpoint deletion
    ########################################################

    def delete(self):
        """
        Delete the streaming endpoint
        """
        return self.client._perform_empty(
            "DELETE", "/projects/%s/streamingendpoints/%s" % (self.project_key, self.streaming_endpoint_name), params = {
            })


    ########################################################
    # Streaming Endpoint definition
    ########################################################

    def get_settings(self):
        """
        Returns the settings of this streaming endpoint as a :class:`DSSStreamingEndpointSettings`, or one of its subclasses.

        Know subclasses of :class:`DSSStreamingEndpointSettings` include :class:`KafkaStreamingEndpointSettings` 
        and :class:`HTTPSSEStreamingEndpointSettings`

        You must use :meth:`~DSSStreamingEndpointSettings.save()` on the returned object to make your changes effective
        on the streaming endpoint.

        .. code-block:: python

            # Example: changing the topic on a kafka streaming endpoint
            streaming_endpoint = project.get_streaming_endpoint("my_endpoint")
            settings = streaming_endpoint.get_settings()
            settings.set_topic("country")
            settings.save()

        :rtype: :class:`DSSStreamingEndpointSettings`
        """
        data = self.client._perform_json("GET", "/projects/%s/streamingendpoints/%s" % (self.project_key, self.streaming_endpoint_name))

        if data["type"] in ['kafka']:
            return KafkaStreamingEndpointSettings(self, data)
        elif data["type"] in ['httpsse']:
            return HTTPSSEStreamingEndpointSettings(self, data)
        else:
            return DSSStreamingEndpointSettings(self, data)

    def exists(self):
        """Returns whether this streaming endpoint exists"""
        try:
            self.get_schema()
            return True
        except Exception as e:
            return False

    ########################################################
    # Streaming Endpoint metadata
    ########################################################

    def get_schema(self):
        """
        Get the schema of the streaming endpoint
        
        Returns:
            a JSON object of the schema, with the list of columns
        """
        return self.client._perform_json(
                "GET", "/projects/%s/streamingendpoints/%s/schema" % (self.project_key, self.streaming_endpoint_name))

    def set_schema(self, schema):
        """
        Set the schema of the streaming endpoint
        
        Args:
            schema: the desired schema for the streaming endpoint, as a JSON object. All columns have to provide their
            name and type
        """
        return self.client._perform_json(
                "PUT", "/projects/%s/streamingendpoints/%s/schema" % (self.project_key, self.streaming_endpoint_name),
                body=schema)

    ########################################################
    # Misc
    ########################################################

    def get_zone(self):
        """
        Gets the flow zone of this streaming endpoint

        :rtype: :class:`dataikuapi.dss.flow.DSSFlowZone`
        """
        return self.project.get_flow().get_zone_of_object(self)

    def move_to_zone(self, zone):
        """
        Moves this object to a flow zone

        :param object zone: a :class:`dataikuapi.dss.flow.DSSFlowZone` where to move the object
        """
        if isinstance(zone, basestring):
            zone = self.project.get_flow().get_zone(zone)
        zone.add_item(self)

    def share_to_zone(self, zone):
        """
        Share this object to a flow zone

        :param object zone: a :class:`dataikuapi.dss.flow.DSSFlowZone` where to share the object
        """
        if isinstance(zone, basestring):
            zone = self.project.get_flow().get_zone(zone)
        zone.add_shared(self)

    def unshare_from_zone(self, zone):
        """
        Unshare this object from a flow zone

        :param object zone: a :class:`dataikuapi.dss.flow.DSSFlowZone` from where to unshare the object
        """
        if isinstance(zone, basestring):
            zone = self.project.get_flow().get_zone(zone)
        zone.remove_shared(self)

    def get_usages(self):
        """
        Get the recipes or analyses referencing this streaming endpoint

        Returns:
            a list of usages
        """
        return self.client._perform_json("GET", "/projects/%s/streamingendpoints/%s/usages" % (self.project_key, self.streaming_endpoint_name))

    ########################################################
    # Discussions
    ########################################################
    def get_object_discussions(self):
        """
        Get a handle to manage discussions on the streaming endpoint

        :returns: the handle to manage discussions
        :rtype: :class:`dataikuapi.discussion.DSSObjectDiscussions`
        """
        return DSSObjectDiscussions(self.client, self.project_key, "STREAMING_ENDPOINT", self.streaming_endpoint_name)

    ########################################################
    # Test / Autofill
    ########################################################

    def test_and_detect(self, infer_storage_types=False, limit=10, timeout=60):
        settings = self.get_settings()

        if settings.type in ['kafka']:
            future_resp = self.client._perform_json("POST",
                "/projects/%s/streamingendpoints/%s/actions/testAndDetectSettings/kafka"% (self.project_key, self.streaming_endpoint_name),
                body = { "inferStorageTypes" : infer_storage_types , "limit" : limit, "timeout" : timeout })

            return DSSFuture(self.client, future_resp.get('jobId', None), future_resp)
        elif settings.type in ['httpsse']:
            future_resp = self.client._perform_json("POST",
                "/projects/%s/streamingendpoints/%s/actions/testAndDetectSettings/httpsse"% (self.project_key, self.streaming_endpoint_name),
                body = { "inferStorageTypes" : infer_storage_types , "limit" : limit, "timeout" : timeout })

            return DSSFuture(self.client, future_resp.get('jobId', None), future_resp)
        else:
            raise ValueError("don't know how to test/detect on streaming endpoint type:%s" % settings.type)

    def autodetect_settings(self, infer_storage_types=False, limit=10, timeout=60):
        settings = self.get_settings()

        if settings.type in ['kafka']:
            future = self.test_and_detect(infer_storage_types, limit, timeout)
            result = future.wait_for_result()

            settings.get_raw()["schema"] = result["schemaDetection"]["detectedSchema"]

            return settings

        elif settings.type in ['httpsse']:
            future = self.test_and_detect(infer_storage_types, limit, timeout)
            result = future.wait_for_result()

            settings.get_raw()["schema"] = result["schemaDetection"]["detectedSchema"]

            return settings

        else:
            raise ValueError("don't know how to test/detect on streaming endpoint type:%s" % settings.type)

    def get_as_core_streaming_endpoint(self):
        import dataiku
        return dataiku.StreamingEndpoint("%s.%s" % (self.project_key, self.streaming_endpoint_name))

    ########################################################
    # Creation of recipes
    ########################################################

    def new_code_recipe(self, type, code=None, recipe_name=None):
        """
        Starts creation of a new code recipe taking this streaming endpoint as input
        :param str type: Type of the recipe ('cpython', 'streaming_spark_scala', ...)
        :param str code: The code of the recipe
        """

        builder = recipe.CodeRecipeCreator(recipe_name, type, self.project)
        builder.with_input(self.streaming_endpoint_name)
        if code is not None:
            builder.with_script(code)
        return builder

    def new_recipe(self, type, recipe_name=None):
        """
        Starts creation of a new recipe taking this streaming endpoint as input.
        For more details, please see :meth:`dataikuapi.dss.project.DSSProject.new_recipe`

        :param str type: Type of the recipe
        """
        builder = self.project.new_recipe(type=type, name=recipe_name)
        builder.with_input(self.streaming_endpoint_name)
        return builder

class DSSStreamingEndpointSettings(object):
    def __init__(self, streaming_endpoint, settings):
        self.streaming_endpoint = streaming_endpoint
        self.settings = settings

    def get_raw(self):
        """Get the raw streaming endpoint settings as a dict"""
        return self.settings

    def get_raw_params(self):
        """Get the type-specific params, as a raw dict"""
        return self.settings["params"]

    @property
    def type(self):
        return self.settings["type"]

    def add_raw_schema_column(self, column):
        self.settings["schema"]["columns"].append(column)

    def save(self):
        self.streaming_endpoint.client._perform_empty(
                "PUT", "/projects/%s/streamingendpoints/%s" % (self.streaming_endpoint.project_key, self.streaming_endpoint.streaming_endpoint_name),
                body=self.settings)

class KafkaStreamingEndpointSettings(DSSStreamingEndpointSettings):
    def __init__(self, streaming_endpoint, settings):
        super(KafkaStreamingEndpointSettings, self).__init__(streaming_endpoint, settings)

    def set_connection_and_topic(self, connection, topic):
        self.settings["params"]["connection"] = connection
        self.settings["params"]["topic"] = topic

class HTTPSSEStreamingEndpointSettings(DSSStreamingEndpointSettings):
    def __init__(self, streaming_endpoint, settings):
        super(HTTPSSEStreamingEndpointSettings, self).__init__(streaming_endpoint, settings)

    def set_url(self, url):
        self.settings["params"]["url"] = url


class DSSManagedStreamingEndpointCreationHelper(object):

    def __init__(self, project, streaming_endpoint_name, streaming_endpoint_type):
        self.project = project
        self.streaming_endpoint_name = streaming_endpoint_name
        self.streaming_endpoint_type = streaming_endpoint_type
        self.creation_settings = {}

    def get_creation_settings(self):
        return self.creation_settings

    def with_store_into(self, connection, format_option_id = None):
        """
        Sets the connection into which to store the new streaming endpoint
        :param str connection: Name of the connection to store into
        :param str format_option_id: Optional identifier of a serialization format option
        :return: self
        """
        self.creation_settings["connectionId"] = connection
        if format_option_id is not None:
            self.creation_settings["formatOptionId"] = format_option_id
        return self


    def create(self, overwrite=False):
        """
        Executes the creation of the streaming endpoint according to the selected options
        :param overwrite: If the streaming endpoint being created already exists, delete it first (removing data)
        :return: The :class:`DSSStreamingEndpoint` corresponding to the newly created streaming endpoint
        """
        if overwrite and self.already_exists():
            self.project.get_streaming_endpoint(self.streaming_endpoint_name).delete()

        self.project.client._perform_json("POST", "/projects/%s/streamingendpoints/managed" % self.project.project_key,
            body = {
                "id": self.streaming_endpoint_name,
                "type": self.streaming_endpoint_type,
                "creationSettings":  self.creation_settings
        })
        return DSSStreamingEndpoint(self.project.client, self.project.project_key, self.streaming_endpoint_name)

    def already_exists(self):
        """Returns whether this streaming endpoint already exists"""
        streaming_endpoint = self.project.get_streaming_endpoint(self.streaming_endpoint_name)
        try:
            streaming_endpoint.get_schema()
            return True
        except Exception as e:
            return False