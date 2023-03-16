from ..utils import DataikuException
from .future import DSSFuture
import json, warnings, logging
from .utils import DSSTaggableObjectListItem
from .future import DSSFuture
from .discussion import DSSObjectDiscussions
from . import recipe

try:
    basestring
except NameError:
    basestring = str

class DSSStreamingEndpointListItem(DSSTaggableObjectListItem):
    """
    An item in a list of streaming endpoints. 

    .. important::

        Do not instantiate this class, use :meth:`.DSSProject.list_streaming_endpoints()` instead
    """
    def __init__(self, client, data):
        super(DSSStreamingEndpointListItem, self).__init__(data)
        self.client = client


    def __repr__(self):
        return u"<{} {}.{}>".format(self.__class__.__name__, self._data["projectKey"], self._data["id"])

    def to_streaming_endpoint(self):
        """
        Get a handle on the corresponding streaming endpoint.

        :rtype: :class:`DSSStreamingEndpoint`
        """
        return DSSStreamingEndpoint(self.client, self._data["projectKey"], self._data["id"])

    @property
    def name(self):
        """
        Get the streaming endpoint name.

        :rtype: string
        """
        return self._data["id"]

    @property
    def id(self):
        """
        Get the streaming endpoint identifier.

        .. note::

            For streaming endpoints, the identifier is equal to its name

        :rtype: string
        """
        return self._data["id"]

    @property
    def type(self):
        """
        Get the streaming endpoint type.

        :returns: the type is the same as the type of the connection that the streaming endpoint uses, ie `Kafka`, `SQS`, `KDBPlus` or `httpsse`
        :rtype: string
        """
        return self._data["type"]

    @property
    def schema(self):
        """
        Get the schema of the streaming endpoint.

        Usage example:

        .. code-block:: python

            # list all endpoints containing columns with a 'PII' in comment
            for endpoint in p.list_streaming_endpoints():
                column_list = endpoint.schema['columns']
                pii_columns = [c for c in column_list if 'PII' in c.get("comment", "")]
                if len(pii_columns) > 0:
                    print("Streaming endpoint %s contains %s PII columns" % (endpoint.id, len(pii_columns)))            

        :returns: a schema, as a dict with a `columns` array, in which each element is a column, itself as a dict of

                    * **name** : the column name
                    * **type** : the column type (smallint, int, bigint, float, double, boolean, date, string)
                    * **length** : the string length
                    * **comment** : user comment about the column

        :rtype: dict
        """
        return self._data["schema"]

    @property
    def connection(self):
        """
        Get the connection on which this streaming endpoint is attached.

        :returns: a connection name, or None for HTTP SSE endpoints
        :rtype: string
        """
        if not "params" in self._data:
            return None
        return self._data["params"].get("connection", None)

    def get_column(self, column):
        """
        Get a column in the schema, by its name.

        :param string column: name of column to find

        :returns: a dict of the column settings or None if column does not exist. Fields are:

                    * **name** : the column name
                    * **type** : the column type (smallint, int, bigint, float, double, boolean, date, string)
                    * **length** : the string length
                    * **comment** : user comment about the column

        :rtype: dict
        """
        matched = [col for col in self.schema["columns"] if col["name"] == column]
        return None if len(matched) == 0 else matched[0]

class DSSStreamingEndpoint(object):
    """
    A streaming endpoint on the DSS instance.
    """
    def __init__(self, client, project_key, streaming_endpoint_name):
        self.client = client
        self.project = client.get_project(project_key)
        self.project_key = project_key
        self.streaming_endpoint_name = streaming_endpoint_name

    @property
    def name(self):
        """
        Get the streaming endpoint name.

        :rtype: string
        """
        return self.streaming_endpoint_name

    @property
    def id(self):
        """
        Get the streaming endpoint identifier.

        .. note::

            For streaming endpoints, the identifier is equal to its name

        :rtype: string
        """
        return self.streaming_endpoint_name

    ########################################################
    # Streaming Endpoint deletion
    ########################################################

    def delete(self):
        """
        Delete the streaming endpoint from the flow, and objects using it (recipes or continuous recipes)

        .. attention::

            This call doesn't delete the underlying streaming data. For example for a Kafka streaming endpoint
            the topic isn't deleted
        """
        return self.client._perform_empty(
            "DELETE", "/projects/%s/streamingendpoints/%s" % (self.project_key, self.streaming_endpoint_name), params = {
            })


    ########################################################
    # Streaming Endpoint definition
    ########################################################

    def get_settings(self):
        """
        Get the settings of this streaming endpoint.

        Know subclasses of :class:`DSSStreamingEndpointSettings` include :class:`KafkaStreamingEndpointSettings` 
        and :class:`HTTPSSEStreamingEndpointSettings`

        You must use :meth:`~DSSStreamingEndpointSettings.save()` on the returned object to make your changes effective
        on the streaming endpoint.

        .. code-block:: python

            # Example: changing the topic on a kafka streaming endpoint
            streaming_endpoint = project.get_streaming_endpoint("my_endpoint")
            settings = streaming_endpoint.get_settings()
            settings.set_connection_and_topic(None, "country")
            settings.save()

        :returns: an object containing the settings
        :rtype: :class:`DSSStreamingEndpointSettings` or a subclass
        """
        data = self.client._perform_json("GET", "/projects/%s/streamingendpoints/%s" % (self.project_key, self.streaming_endpoint_name))

        if data["type"] in ['kafka']:
            return KafkaStreamingEndpointSettings(self, data)
        elif data["type"] in ['httpsse']:
            return HTTPSSEStreamingEndpointSettings(self, data)
        else:
            return DSSStreamingEndpointSettings(self, data)

    def exists(self):
        """
        Whether this streaming endpoint exists in DSS.

        :rtype: boolean
        """
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
        Get the schema of the streaming endpoint.
        
        :returns: a schema, as a dict with a `columns` array, in which each element is a column, itself as a dict of

                    * **name** : the column name
                    * **type** : the column type (smallint, int, bigint, float, double, boolean, date, string)
                    * **comment** : user comment about the column

        :rtype: dict
        """
        return self.client._perform_json(
                "GET", "/projects/%s/streamingendpoints/%s/schema" % (self.project_key, self.streaming_endpoint_name))

    def set_schema(self, schema):
        """
        Set the schema of the streaming endpoint.

        Usage example:

        .. code-block:: python

            # copy schema of the input of a continuous recipe to its output
            recipe = p.get_recipe('my_recipe_name')
            recipe_settings = recipe.get_settings()
            input_endpoint = p.get_streaming_endpoint(recipe_settings.get_flat_input_refs()[0])
            output_endpoint = p.get_streaming_endpoint(recipe_settings.get_flat_output_refs()[0])
            output_endpoint.set_schema(input_endpoint.get_schema())

        
        :param dict schema: a schema, as a dict with a `columns` array, in which each element is a column, itself as a dict of

                                * **name** : the column name
                                * **type** : the column type (smallint, int, bigint, float, double, boolean, date, string)
                                * **comment** : user comment about the column
        """
        return self.client._perform_json(
                "PUT", "/projects/%s/streamingendpoints/%s/schema" % (self.project_key, self.streaming_endpoint_name),
                body=schema)

    ########################################################
    # Misc
    ########################################################

    def get_zone(self):
        """
        Get the flow zone of this streaming endpoint.

        :returns: a flow zone
        :rtype: :class:`dataikuapi.dss.flow.DSSFlowZone`
        """
        return self.project.get_flow().get_zone_of_object(self)

    def move_to_zone(self, zone):
        """
        Move this object to a flow zone.

        :param object zone: a :class:`dataikuapi.dss.flow.DSSFlowZone` where to move the object, or its identifier
        """
        if isinstance(zone, basestring):
            zone = self.project.get_flow().get_zone(zone)
        zone.add_item(self)

    def share_to_zone(self, zone):
        """
        Share this object to a flow zone.

        :param object zone: a :class:`dataikuapi.dss.flow.DSSFlowZone` where to share the object, or its identifier
        """
        if isinstance(zone, basestring):
            zone = self.project.get_flow().get_zone(zone)
        zone.add_shared(self)

    def unshare_from_zone(self, zone):
        """
        Unshare this object from a flow zone.

        :param object zone: a :class:`dataikuapi.dss.flow.DSSFlowZone` from where to unshare the object, or its identifier
        """
        if isinstance(zone, basestring):
            zone = self.project.get_flow().get_zone(zone)
        zone.remove_shared(self)

    def get_usages(self):
        """
        Get the recipes referencing this streaming endpoint.

        Usage example:

        .. code-block:: python

            for usage in streaming_endpoint.get_usages():
                if usage["type"] == 'RECIPE_INPUT':
                    print("Used as input of %s" % usage["objectId"])

        :returns: a list of usages, each one a dict of:

                     * **type** : the type of usage, either "RECIPE_INPUT" or "RECIPE_OUTPUT"
                     * **objectId** : name of the recipe or continuous recipe
                     * **objectProjectKey** : project of the recipe or continuous recipe

        :rtype: list[dict]
        """
        return self.client._perform_json("GET", "/projects/%s/streamingendpoints/%s/usages" % (self.project_key, self.streaming_endpoint_name))

    ########################################################
    # Discussions
    ########################################################
    def get_object_discussions(self):
        """
        Get a handle to manage discussions on the streaming endpoint.

        :returns: the handle to manage discussions
        :rtype: :class:`dataikuapi.dss.discussion.DSSObjectDiscussions`
        """
        return DSSObjectDiscussions(self.client, self.project_key, "STREAMING_ENDPOINT", self.streaming_endpoint_name)

    ########################################################
    # Test / Autofill
    ########################################################

    def test_and_detect(self, infer_storage_types=False, limit=10, timeout=60):
        """
        Used internally by :meth:`autodetect_settings`. It is not usually required to call this method

        .. attention::

            Only Kafka and HTTP-SSE streaming endpoints are handled

        .. note::

            Schema inferrence is done on the captured rows from the underlying stream. If no record is
            captured, for example because no message is posted to the stream while the capture is done,
            then no schema inferrence can take place.

        :returns: a future object on the result of the detection. The future's result is a dict with fields:

                    * **table** : the captured rows
                    * **schemaDetection** : the result of the schema inference. Notable sub-fields are

                      * **detectedSchema** : the inferred schema
                      * **detectedButNotInSchema** : list of column names found in the capture, but not yet in the endpoint's schema
                      * **inSchemaButNotDetected** : list of column names present in the endpoint's schema, but not found in the capture

        :rtype: :class:`dataikuapi.dss.future.DSSFuture`
        """
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
        """
        Detect an appropriate schema for this streaming endpoint using Dataiku detection engine.

        The detection bases itself on a capture of the stream that this streaming endpoint represents. First
        a number of messages are captured from the stream, within the bounds passed as parameters, then a
        detection of the columns and their types is done on the captured messages. If no message is send on
        the stream during the capture, no column is inferred.

        .. attention::

            Only Kafka and HTTP-SSE streaming endpoints are handled

        .. note::

            Format-related settings are not automatically inferred. For example the method will
            not detect whether Kafka messages are JSON-encoded or Avro-encoded

        Usage example:

        .. code-block:: python

            # create a kafka endpoint on a json stream and detect its schema
            e = project.create_kafka_streaming_endpoint('test_endpoint', 'kafka_connection', 'kafka-topic')
            s = e.autodetect_settings(infer_storage_types=True)
            s.save()

        :param boolean infer_storage_types: if True, DSS will try to guess types of the columns. If False, all columns
                                            will be assumed to be strings (default: False)
        :param int limit: max number of rows to use for the autodetection (default: 10)
        :param int timeout: max duration in seconds of the stream capture to use for the autodetection (default: 60)

        :returns: streaming endpoint settings with an updated schema that you can :meth:`DSSStreamingEndpointSettings.save`.
        :rtype: :class:`DSSStreamingEndpointSettings` or a subclass
        """
        settings = self.get_settings()

        if settings.type in ['kafka']:
            future = self.test_and_detect(infer_storage_types, limit, timeout)
            result = future.wait_for_result()

            if result.get("schemaDetection", {}).get("detectedSchema") is None:
                logging.warn("No schema detected, leaving existing schema")
            else:
                settings.get_raw()["schema"] = result["schemaDetection"]["detectedSchema"]

            return settings

        elif settings.type in ['httpsse']:
            future = self.test_and_detect(infer_storage_types, limit, timeout)
            result = future.wait_for_result()

            if result.get("schemaDetection", {}).get("detectedSchema") is None:
                logging.warn("No schema detected, leaving existing schema")
            else:
                settings.get_raw()["schema"] = result["schemaDetection"]["detectedSchema"]

            return settings

        else:
            raise ValueError("don't know how to test/detect on streaming endpoint type:%s" % settings.type)

    def get_as_core_streaming_endpoint(self):
        """
        Get the streaming endpoint as a handle for use inside DSS.

        :returns: the streaming endpoint
        :rtype: :class:`dataiku.StreamingEndpoint`
        """
        import dataiku
        return dataiku.StreamingEndpoint("%s.%s" % (self.project_key, self.streaming_endpoint_name))

    ########################################################
    # Creation of recipes
    ########################################################

    def new_code_recipe(self, type, code=None, recipe_name=None):
        """
        Start the creation of a new code recipe taking this streaming endpoint as input.

        Usage example:

        .. code-block:: python

            # create a continuous python recipe from an endpoint
            recipe_creator = endpoint.new_code_recipe('cpython', 'some code here', 'compute_something')
            recipe_creator.with_new_output_streaming_endpoint('something', 'my_kafka_connection', 'avro')
            recipe = recipe_creator.create()

        :param string type: type of the recipe. Can be 'cpython', 'streaming_spark_scala' or 'ksql'; the
                            non-continuous type 'python' is also possible
        :param string code: (optional) The script of the recipe
        :param string recipe_name: (optional) base name for the new recipe.

        :returns: an object to create a new recipe
        :rtype: :class:`dataikuapi.dss.recipe.CodeRecipeCreator`
        """

        builder = recipe.CodeRecipeCreator(recipe_name, type, self.project)
        builder.with_input(self.streaming_endpoint_name)
        if code is not None:
            builder.with_script(code)
        return builder

    def new_recipe(self, type, recipe_name=None):
        """
        Start the creation of a new recipe taking this streaming endpoint as input.

        This method can create non-code recipes like Sync or continuous Sync recipes. For more details, please
        see :meth:`dataikuapi.dss.project.DSSProject.new_recipe`.

        Usage example:

        .. code-block:: python

            # create a continuous sync from an endpoint to a dataset
            recipe_creator = endpoint.new_recipe('csync', 'compute_my_dataset_name')
            recipe_creator.with_new_output('my_dataset_name', 'filesystem_managed')
            recipe = recipe_creator.create()

        :param string type: type of the recipe. Possible values are 'csync', 'cpython', 'python', 'ksql', 'streaming_spark_scala'
        :param string recipe_name: (optional) base name for the new recipe.

        :returns: A new DSS Recipe Creator handle
        :rtype: :class:`dataikuapi.dss.recipe.DSSRecipeCreator` or a subclass
        """
        builder = self.project.new_recipe(type=type, name=recipe_name)
        builder.with_input(self.streaming_endpoint_name)
        return builder

class DSSStreamingEndpointSettings(object):
    """
    Base settings class for a DSS streaming endpoint.

    .. important::

        Do not instantiate this class directly, use :meth:`DSSStreamingEndpoint.get_settings`

    Use :meth:`save` to save your changes
    """

    def __init__(self, streaming_endpoint, settings):
        self.streaming_endpoint = streaming_endpoint
        self.settings = settings

    def get_raw(self):
        """
        Get the streaming endpoint settings as a dict.

        :returns: the settings. Top-level fields are:

                    * **id** : the name (used as identifier) of the streaming endpoint
                    * **type** : the type of the connection underlying the streaming endpoint (Kafka, SQS, ...)
                    * **params** : the type-specific parameters, as a dict. Depend on the connection type
                    * **tags** : list of tags, each a string
                    * **schema** : the columns of the streaming endpoing, as a dict with a `columns` array, in which each element is a column, itself as a dict of

                        * **name** : the column name
                        * **type** : the column type (smallint, int, bigint, float, double, boolean, date, string)
                        * **length** : the string length
                        * **comment** : user comment about the column

        :rtype: dict
        """
        return self.settings

    def get_raw_params(self):
        """
        Get the type-specific (Kafka/ HTTP-SSE/ Kdb+...) params as a dict.

        :returns: the type-specific params. Each type defines a set of fields; commonly found fields are :

                    * **connection** : name of the connection used by the streaming endpoint
                    * **topic** or **queueName** : name of the Kafka topic or SQS queue corresponding to this streaming endpoint

        :rtype: dict
        """
        return self.settings["params"]

    @property
    def type(self):
        """
        Get the type of streaming system that the streaming endpoint uses.

        :return: a type of streaming system. Possible values: 'kafka', 'SQS', 'kdbplustick', 'httpsse'
        :rtype: string
        """
        return self.settings["type"]

    def add_raw_schema_column(self, column):
        """
        Add a column in the schema

        :param dict column: a dict defining the column. It should contain a "name" field and a "type" field (with a DSS type, like bigint, double, string, date, boolean, ...), optionally a "length" field for string-typed columns and a "comment" field.
        """
        self.settings["schema"]["columns"].append(column)

    def save(self):
        """
        Save the changes to the settings on the streaming endpoint.
        """
        self.streaming_endpoint.client._perform_empty(
                "PUT", "/projects/%s/streamingendpoints/%s" % (self.streaming_endpoint.project_key, self.streaming_endpoint.streaming_endpoint_name),
                body=self.settings)

class KafkaStreamingEndpointSettings(DSSStreamingEndpointSettings):
    """
    Settings for a Kafka streaming endpoint. 

    This class inherits from :class:`DSSStreamingEndpointSettings`.
    
    .. important::

        Do not instantiate this class directly, use :meth:`DSSStreamingEndpoint.get_settings`

    Use :meth:`save` to save your changes
    """
    def __init__(self, streaming_endpoint, settings):
        super(KafkaStreamingEndpointSettings, self).__init__(streaming_endpoint, settings)

    def set_connection_and_topic(self, connection=None, topic=None):
        """
        Change the connection and topic of an endpoint.

        :param string connection: (optional) name of a Kafka connection in DSS
        :param string topic: (optional) name of a Kafka topic. Can contain DSS variables
        """
        if connection is not None:
            self.settings["params"]["connection"] = connection
        if topic is not None:
            self.settings["params"]["topic"] = topic

class HTTPSSEStreamingEndpointSettings(DSSStreamingEndpointSettings):
    """
    Settings for a HTTP-SSE streaming endpoint. 

    This class inherits from :class:`DSSStreamingEndpointSettings`.
    
    .. important::

        Do not instantiate this class directly, use :meth:`DSSStreamingEndpoint.get_settings`

    Use :meth:`save` to save your changes
    """
    def __init__(self, streaming_endpoint, settings):
        super(HTTPSSEStreamingEndpointSettings, self).__init__(streaming_endpoint, settings)

    def set_url(self, url):
        """
        Change the URL of the endpoint.

        :param string url: url to connect to
        """
        self.settings["params"]["url"] = url


class DSSManagedStreamingEndpointCreationHelper(object):
    """
    Utility class to help create a new streaming endpoint.

    .. note::

        Do not instantiate directly, use :meth:`.DSSProject.new_managed_streaming_endpoint()` instead

    .. important::

        Only Kafka and SQS endpoints support managed streaming endpoints
    """

    def __init__(self, project, streaming_endpoint_name, streaming_endpoint_type):
        self.project = project
        self.streaming_endpoint_name = streaming_endpoint_name
        self.streaming_endpoint_type = streaming_endpoint_type
        self.creation_settings = {}

    def get_creation_settings(self):
        """
        Get the settings for the creation of the new managed streaming endpoint.

        .. note::

            Modifying the values in the creation settings directly is discouraged, use :meth:`with_store_into()`
            instead.

        :returns: the settings as a dict
        :rtype: dict
        """
        return self.creation_settings

    def with_store_into(self, connection, format_option_id = None):
        """
        Set the DSS connection underlying the new streaming endpoint.

        :param string connection: name of the connection to store into
        :param string format_option_id: (optional) identifier of a serialization format option. For Kafka endpoints, possible 
                                        values are :

                                          * **json** : messages are JSON strings
                                          * **single** : messages are handled as a single typed field
                                          * **avro** : messages are Kafka-Avro messages (ie an avro message padded with a field indicating the avro schema version in the kafka schema registry)

                                        For SQS endpoints, possible values are

                                          * **json** : messages are JSON strings
                                          * **string** : messages are raw strings
        :returns: self
        """
        self.creation_settings["connectionId"] = connection
        if format_option_id is not None:
            self.creation_settings["formatOptionId"] = format_option_id
        return self


    def create(self, overwrite=False):
        """
        Execute the creation of the streaming endpoint according to the selected options

        :param boolean overwrite: If the streaming endpoint being created already exists, delete it first

        :returns: an object corresponding to the newly created streaming endpoint
        :rtype: :class:`DSSStreamingEndpoint`
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
        """
        Whether the desired name for the new streaming endpoint is already used by another streaming endpoint

        :rtype: boolean
        """
        streaming_endpoint = self.project.get_streaming_endpoint(self.streaming_endpoint_name)
        try:
            streaming_endpoint.get_schema()
            return True
        except Exception as e:
            return False