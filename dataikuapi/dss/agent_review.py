from dataikuapi.dss.future import DSSFuture, DSSFutureWithHistory
from dataikuapi.dss.utils import DSSTaggableObjectListItem


class DSSAgentReviewTrait(dict):
    """
    Represents the configuration of a trait for an agent review.
    """

    def __init__(self, data=None, **kwargs):
        super(DSSAgentReviewTrait, self).__init__(data or {}, **kwargs)

    @property
    def id(self):
        """
        The unique identifier of the trait.
        :rtype: str
        """
        return self.get("id")

    @property
    def name(self):
        """
        The name of the trait.
        :rtype: str
        """
        return self.get("name")

    @name.setter
    def name(self, value):
        self["name"] = value

    @property
    def description(self):
        """
        The description of the trait.
        :rtype: str
        """
        return self.get("description")

    @description.setter
    def description(self, value):
        self["description"] = value

    @property
    def llm_id(self):
        """
        The ID of the LLM used to compute this trait.
        :rtype: str
        """
        return self.get("llmId")

    @llm_id.setter
    def llm_id(self, value):
        self["llmId"] = value

    @property
    def criteria(self):
        """
        The criteria or prompt used by the LLM to evaluate this trait.
        :rtype: str
        """
        return self.get("criteria")

    @criteria.setter
    def criteria(self, value):
        self["criteria"] = value

    @property
    def enabled(self):
        """
        Whether this trait is enabled for the agent review.
        :rtype: bool
        """
        return self.get("enabled")

    @enabled.setter
    def enabled(self, value):
        self["enabled"] = value

    @property
    def needs_reference(self):
        """
        Whether this trait requires a reference answer to be computed.
        :rtype: bool
        """
        return self.get("needsReference")

    @needs_reference.setter
    def needs_reference(self, value):
        self["needsReference"] = value

    @property
    def needs_expectations(self):
        """
        Whether this trait requires expectations to be computed.
        :rtype: bool
        """
        return self.get("needsExpectations")

    @needs_expectations.setter
    def needs_expectations(self, value):
        self["needsExpectations"] = value

    def __repr__(self):
        return "DSSAgentReviewTrait(id=%r, name=%r, description=%r, llm_id=%r, criteria=%r, enabled=%r, needs_reference=%r, needs_expectations=%r)" % (
            self.id, self.name, self.description, self.llm_id, self.criteria, self.enabled, self.needs_reference, self.needs_expectations
        )


class DSSAgentReview(object):
    """
    A handle to interact with an agent review on the DSS instance.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.get_agent_review` instead
    """

    def __init__(self, dss_client, project_key, data):
        self.dss_client = dss_client
        self.project_key = project_key
        self.data = data

    @property
    def id(self):
        """
        Unique ID of the agent review.
        :rtype: str
        """
        return self.data.get("id")

    @property
    def name(self):
        """
        Name of the agent review.
        :rtype: str
        """
        return self.data.get("name")

    @name.setter
    def name(self, value):
        self.data["name"] = value

    @property
    def owner(self):
        """
        The owner of the agent review.
        :return:
        """
        return self.data.get("owner")

    @property
    def creation_timestamp(self):
        """
        Timestamp of creation (epoch millis).
        :rtype: int
        """
        return self.data.get("creationTimestamp")

    @property
    def agent_id(self):
        """
        ID of the associated agent (Saved Model smart ID).
        :rtype: str
        """
        return self.data.get("agentSmartId")

    @agent_id.setter
    def agent_id(self, value):
        self.data["agentSmartId"] = value

    @property
    def agent_version(self):
        """
        Version of the associated agent.
        :rtype: str
        """
        return self.data.get("agentVersion")

    @property
    def traits(self):
        """
        Traits of the agent review.
        :rtype: list of :class:`DSSAgentReviewTrait`
        """
        return [DSSAgentReviewTrait(data) for data in self.data.get("traits", [])]

    @traits.setter
    def traits(self, traits):
        self.data["traits"] = traits

    @property
    def helper_llm_id(self):
        """
        Id of the "helper" LLM, used to compute expectations
        :rtype: str
        """
        return self.data.get("helperLLMId")

    @helper_llm_id.setter
    def helper_llm_id(self, value):
        self.data["helperLLMId"] = value

    @property
    def nb_executions(self):
        """
        Number of times a test is executed in a run
        :rtype: int
        """
        return self.data.get("nbExecutions")

    @nb_executions.setter
    def nb_executions(self, value):
        self.data["nbExecutions"] = value

    @property
    def hitl_validation_policy(self):
        """
        Review-wide default HITL validation policy used when creating a test.
        Possible values are ``ACCEPT`` or ``REJECT``.
        :rtype: str
        """
        return self.data.get("hitlValidationPolicy")

    @hitl_validation_policy.setter
    def hitl_validation_policy(self, value):
        self.data["hitlValidationPolicy"] = value

    @property
    def hitl_max_validation_turns(self):
        """
        Maximum number of validation turns auto-answered during a test run before stopping.
        Possible values are integers greater than or equal to ``1``.
        :rtype: int
        """
        return self.data.get("hitlMaxValidationTurns")

    @hitl_max_validation_turns.setter
    def hitl_max_validation_turns(self, value):
        self.data["hitlMaxValidationTurns"] = value

    def get_trait(self, trait_id):
        """
        Get a specific trait by its ID.
        :param str trait_id: ID of the trait to retrieve.
        :returns: The requested trait, or None if not found.
        :rtype: :class:`DSSAgentReviewTrait`
        """
        for trait in self.traits:
            if trait.id == trait_id:
                return trait
        return None

    def add_trait(self, trait):
        """
        Add a trait to this agent review configuration.
        :param trait: The trait to add.
        :type trait: :class:`DSSAgentReviewTrait` or dict
        """
        if self.data.get("traits"):
            self.data.get("traits").append(trait)
        else:
            self.data["traits"] = [trait]

    def get_raw(self):
        """
        Get the raw agent review data.
        :rtype: dict
        """
        return self.data

    @agent_version.setter
    def agent_version(self, value):
        self.data["agentVersion"] = value

    def list_tests(self, as_type='listitems'):
        """
        List all tests linked to this agent review.

        :param str as_type: Type of objects to return. Can be 'listitems' (default) or 'objects'.
        :returns: List of tests defined for this agent review.
        :rtype: if as_type=listitems, each test as a :class:`dataikuapi.dss.agent_review.DSSAgentReviewTestListItem`.
                if as_type=objects, each test is returned as a :class:`dataikuapi.dss.agent_review.DSSAgentReviewTest`.
        """
        tests = self.dss_client._perform_json(
            "GET", "/projects/%s/agent-reviews/reviews/%s/tests" % (self.project_key, self.id)
        )
        if as_type == 'listitems':
            return [DSSAgentReviewTestListItem(self.dss_client, self.project_key, test) for test in tests]
        if as_type == 'objects':
            return [DSSAgentReviewTest(self.dss_client, self.project_key, test) for test in tests]

    def get_test(self, test_id):
        """
        Get a specific test by its ID.

        :param str test_id: ID of the test to retrieve.
        :returns: The requested test.
        :rtype: :class:`DSSAgentReviewTest`
        """
        test = self.dss_client._perform_json(
            "GET", "/projects/%s/agent-reviews/tests/%s" % (self.project_key, test_id)
        )
        return DSSAgentReviewTest(self.dss_client, self.project_key, test)

    def create_test(self, query=None, reference_answer=None, expectations=None, hitl_validation_policy=None):
        """
        Create a new test for this agent review.

        :param str query: Query to test the agent. Optional.
        :param str reference_answer: Reference answer. Optional.
        :param str expectations: Expectations on the agent answer. Optional.
        :param str hitl_validation_policy: Per-test HITL validation policy. Optional.
        :returns: The created test object.
        :rtype: :class:`DSSAgentReviewTest`
        """
        body = {
            "projectKey": self.project_key,
            "agentReviewId": self.id,
            "query": query,
            "referenceAnswer": reference_answer,
            "expectations": expectations,
            "hitlValidationPolicy": hitl_validation_policy,
        }
        test = self.dss_client._perform_json(
            "POST", "/projects/%s/agent-reviews/tests" % self.project_key, body=body
        )
        return DSSAgentReviewTest(self.dss_client, self.project_key, test)

    def create_tests_from_dataset(self, full_dataset_name, query_column, reference_answer_column=None, expectations_column=None, top_n=None, partitions=None, latest_partitions_n=None, hitl_validation_policy_column=None):
        """
        Create new tests for this agent review by importing them from a dataset.

        :param str full_dataset_name: Source dataset name.
        :param str query_column: Name of the column containing the queries.
        :param str reference_answer_column: Name of the column containing the reference answers. Optional.
        :param str expectations_column: Name of the column containing the expectations. Optional.
        :param int top_n: Only take the first n rows of the dataset. Optional.
        :param list[str] partitions: For partitioned datasets, only consider the given partitions. Optional.
        :param int latest_partitions_n: For partitioned datasets and if partitions is not set, only consider the latest n partitions. Optional.
        :param str hitl_validation_policy_column: Name of the column containing per-test HITL validation policy. Optional.
        :returns: A dictionary with keys:
            - "createdTestIds": list of ids of the created tests
            - "error": The error message if any occurred
        :rtype: dict
        """
        params = {
            "fullDatasetName": full_dataset_name
        }

        body = {
            "queryColumn": query_column,
            "referenceAnswerColumn": reference_answer_column,
            "expectationsColumn": expectations_column,
            "hitlValidationPolicyColumn": hitl_validation_policy_column,
        }
        if top_n is not None:
            body["samplingMethod"] = "HEAD_SEQUENTIAL"
            body["maxRecords"] = top_n
        else:
            body["samplingMethod"] = "FULL"

        if partitions is not None:
            body["partitionSelectionMethod"] = "SELECTED"
            body["selectedPartitions"] = partitions
        elif latest_partitions_n is not None:
            body["partitionSelectionMethod"] = "LATEST_N"
            body["latestPartitionsN"] = latest_partitions_n
        else:
            body["partitionSelectionMethod"] = "ALL"

        future_resp = self.dss_client._perform_json(
            "POST", "/projects/%s/agent-reviews/reviews/%s/tests/actions/create-from-dataset" % (self.project_key, self.id), params=params, body=body
        )
        return DSSFuture.get_result_wait_if_needed(self.dss_client, future_resp)

    def export_tests_to_dataset(self, full_dataset_name, create_new_dataset=False, target_connection=None, test_ids=None):
        """
        Export tests of this agent review to a dataset.

        :param str full_dataset_name: Target dataset name.
        :param bool create_new_dataset: set to True to create a new dataset.
        :param str target_connection: If creating a new dataset, ID of the connection to use. Optional.
        :param list[str] test_ids: IDs of the tests to export. If None or empty, exports everything. Optional.
        :returns: A dictionary with keys:
            - "exportedTestCount": count of exported tests
            - "error": The error message if any occurred
        :rtype: dict
        """
        params = {
            "fullDatasetName": full_dataset_name
        }

        body = {
            "overwriteDestinationDataset": not create_new_dataset,
            "destinationDatasetConnection": target_connection,
            "testIds": test_ids,
        }
        future_resp = self.dss_client._perform_json(
            "POST", "/projects/%s/agent-reviews/reviews/%s/tests/actions/export-to-dataset" % (self.project_key, self.id), params=params, body=body
        )
        return DSSFuture.get_result_wait_if_needed(self.dss_client, future_resp)

    def perform_run(self, test_ids=None, wait=True, run_name=None):
        """
        Execute a run with the specified tests.

        :param list[str] test_ids: List of test IDs to run. Optional. If None or empty, all tests will be run.
        :param bool wait: If True, the call blocks until the run is finished. If False, it returns a future history handle. Defaults to True.
        :param str run_name: Optional name for the run.
        :returns: The run object if wait=True, or a future history handle if wait=False.
        :rtype: :class:`DSSAgentReviewRun` or :class:`dataikuapi.dss.future.DSSFutureWithHistory`
        """
        params = {
            "testIds": test_ids or [],
            "wait": wait,
            "runName": run_name
        }
        run_data = self.dss_client._perform_json(
            "POST", "/projects/%s/agent-reviews/reviews/%s/runs" % (self.project_key, self.id), params=params
        )
        if wait:
            return DSSAgentReviewRun(self.dss_client, self.project_key, run_data)
        else:
            # Name format must match AgentReviewRun.java getFutureHistoryKey()
            future_name = "agent-review-%s-%s-%s" % (self.project_key, self.id, run_data.get("id"))
            return DSSFutureWithHistory(self.dss_client, future_name, result_wrapper=lambda data: DSSAgentReviewRun(self.dss_client, self.project_key, data))

    def list_runs(self, as_type='listitems'):
        """
        List all runs of this agent review.

        :param str as_type: Type of objects to return. Can be 'listitems' (default) or 'objects'.
        :returns: List of runs.
        :rtype: if as_type=listitems, each run as a :class:`DSSAgentReviewRunListItem`.
                if as_type=objects, each run is returned as a :class:`DSSAgentReviewRun`.
        """
        runs = self.dss_client._perform_json(
            "GET", "/projects/%s/agent-reviews/reviews/%s/runs" % (self.project_key, self.id)
        )
        if as_type == 'listitems':
            return [DSSAgentReviewRunListItem(self.dss_client, self.project_key, run) for run in runs]
        if as_type == 'objects':
            return [DSSAgentReviewRun(self.dss_client, self.project_key, run) for run in runs]

    def get_run(self, run_id):
        """
        Get a specific run by its ID.

        :param str run_id: ID of the run to retrieve.
        :returns: The requested run.
        :rtype: :class:`DSSAgentReviewRun`
        """
        run = self.dss_client._perform_json(
            "GET", "/projects/%s/agent-reviews/reviews/%s/runs/%s" % (self.project_key, self.id, run_id)
        )
        return DSSAgentReviewRun(self.dss_client, self.project_key, run)

    def save(self):
        """
        Save the agent review settings.
        :returns: The updated agent review.
        :rtype: :class:`DSSAgentReview`
        """
        result_dict = self.dss_client._perform_json("POST", "/projects/%s/agent-reviews/reviews" % self.project_key,
                                                    body=self.get_raw())
        return DSSAgentReview(self.dss_client, self.project_key, result_dict)

    def delete(self):
        """
        Delete this agent review.
        """
        params = {"agentReviewId": self.id}
        self.dss_client._perform_empty(
            "DELETE", "/projects/%s/agent-reviews/reviews/%s" % (self.project_key, self.id), params=params
        )


class DSSAgentReviewListItem(DSSTaggableObjectListItem):
    """
    An item in a list of agent reviews.

    .. important::

        Do not instantiate this class directly.
        Instances are returned by :meth:`dataikuapi.dss.project.DSSProject.list_agent_reviews()`.
    """

    def __init__(self, dss_client, project_key, data):
        """
        Initialize an agent review list item.

        :param dss_client: DSS client instance
        :param str project_key: Project identifier
        :param dict data: Review metadata
        """
        super(DSSAgentReviewListItem, self).__init__(data)
        self.dss_client = dss_client
        self.project_key = project_key
        self.data = data

    def to_agent_review(self):
        """
        Get a handle to interact with this agent review.

        :returns: A handle on the agent review.
        :rtype: :class:`DSSAgentReview`
        """
        return DSSAgentReview(self.dss_client, self.project_key, self.data)

    @property
    def id(self):
        """
        Unique ID of the agent review.
        :rtype: str
        """
        return self.data.get("id")

    @property
    def name(self):
        """
        Name of the agent review.
        :rtype: str
        """
        return self.data.get("name")

    @property
    def agent_id(self):
        """
        ID of the associated agent (Saved Model smart ID).
        :rtype: str
        """
        return self.data.get("agentSmartId")

    @property
    def agent_version(self):
        """
        Version of the associated agent.
        :rtype: str
        """
        return self.data.get("agentVersion")


class DSSAgentReviewTest(object):
    """
    Represents a single test in an agent review.

    .. important::

        Do not instantiate this class directly.
        Instances are returned by :meth:`DSSAgentReview.list_tests()` or
        :meth:`DSSAgentReview.create_test()`.
    """

    def __init__(self, dss_client, project_key, data):
        """
        Initialize a test.

        :param dss_client: DSS client instance
        :param str project_key: Project identifier
        :param dict data: Test data
        """
        self.dss_client = dss_client
        self.project_key = project_key
        self.data = data

    @property
    def id(self):
        """
        Unique ID of the test.
        :rtype: str
        """
        return self.data.get("id")

    @property
    def agent_review_id(self):
        """
        ID of the associated agent review.
        :rtype: str
        """
        return self.data.get("agentReviewId")

    @property
    def query(self):
        """
        Test query.
        :rtype: str
        """
        return self.data.get("query")

    @query.setter
    def query(self, value):
        self.data["query"] = value

    @property
    def reference_answer(self):
        """
        Expected result of the query.
        :rtype: str
        """
        return self.data.get("referenceAnswer")

    @reference_answer.setter
    def reference_answer(self, value):
        self.data["referenceAnswer"] = value

    @property
    def expectations(self):
        """
        Expectations on the agent answer.
        :rtype: str
        """
        return self.data.get("expectations")

    @expectations.setter
    def expectations(self, value):
        self.data["expectations"] = value

    @property
    def hitl_validation_policy(self):
        """
        Per-test HITL validation policy.
        Possible values are ``ACCEPT`` or ``REJECT``.
        :rtype: str
        """
        return self.data.get("hitlValidationPolicy")

    @hitl_validation_policy.setter
    def hitl_validation_policy(self, value):
        self.data["hitlValidationPolicy"] = value

    @property
    def creation_timestamp(self):
        """
        Timestamp of creation (epoch millis).
        :rtype: int
        """
        return self.data.get("creationTimestamp")

    @property
    def created_by(self):
        """
        Login of the user who created the test.
        :rtype: str
        """
        return self.data.get("createdBy")

    @property
    def last_modification_timestamp(self):
        """
        Timestamp of last modification (epoch millis).
        :rtype: int
        """
        return self.data.get("lastModifiedTimestamp")

    @property
    def last_modified_by(self):
        """
        Login of the user who modified last.
        :rtype: str
        """
        return self.data.get("lastModifiedBy")


    def get_raw(self):
        """
        Get the raw test data.
        :rtype: dict
        """
        return self.data

    def run(self):
        """
        Execute a run with this single test.

        :returns: The created run object.
        :rtype: :class:`DSSAgentReviewRun`
        """
        params = {
            "testIds": [self.id]
        }
        run = self.dss_client._perform_json(
            "POST", "/projects/%s/agent-reviews/reviews/%s/runs" % (self.project_key, self.agent_review_id), params=params
        )
        return DSSAgentReviewRun(self.dss_client, self.project_key, run)

    def save(self):
        """
        Save the test settings.

        :returns: The updated test.
        :rtype: :class:`DSSAgentReviewTest`
        """

        result_dict = self.dss_client._perform_json("PUT",
                                                    "/projects/%s/agent-reviews/tests/%s" % (self.project_key, self.id),
                                                    body=self.get_raw())
        return DSSAgentReviewTest(self.dss_client, self.project_key, result_dict)

    def delete(self):
        """
        Delete this test.
        """
        self.dss_client._perform_empty(
            "DELETE", "/projects/%s/agent-reviews/tests/%s" % (self.project_key, self.id)
        )


class DSSAgentReviewTestListItem(dict):
    """
    An item in a list of agent review tests.

    .. important::

        Do not instantiate this class directly.
        Instances are returned by :meth:`DSSAgentReview.list_tests()`.
    """

    def __init__(self, dss_client, project_key, data):
        """
        Initialize an agent review test list item.

        :param dss_client: DSS client instance
        :param str project_key: Project identifier
        :param dict data: Test metadata
        """
        super().__init__(data)
        self.dss_client = dss_client
        self.project_key = project_key

    def to_agent_review_test(self):
        """
        Get a handle to interact with this agent review test.

        :returns: A handle on the agent review test.
        :rtype: :class:`DSSAgentReviewTest`
        """
        return DSSAgentReviewTest(self.dss_client, self.project_key, self)

    def delete(self):
        """
        Delete this test.
        """
        self.dss_client._perform_empty(
            "DELETE", "/projects/%s/agent-reviews/tests/%s" % (self.project_key, self.id)
        )

    @property
    def id(self):
        """
        Unique ID of the test.
        :rtype: str
        """
        return self.get("id")

    @property
    def query(self):
        """
        Test query.
        :rtype: str
        """
        return self.get("query")

    @property
    def reference_answer(self):
        """
        Expected result of the query.
        :rtype: str
        """
        return self.get("referenceAnswer")

    @property
    def expectations(self):
        """
        Expectations on the agent answer.
        :rtype: str
        """
        return self.get("expectations")

    @property
    def hitl_validation_policy(self):
        """
        Per-test HITL validation policy.
        Possible values are ``ACCEPT`` or ``REJECT``.
        :rtype: str
        """
        return self.get("hitlValidationPolicy")


class DSSAgentReviewRun(object):
    """
    Represents a run of an agent review (execution of tests).

    .. important::

        Do not instantiate this class directly.
        Instances are returned by :meth:`DSSAgentReview.get_run()`.
    """

    def __init__(self, dss_client, project_key, data):
        """
        Initialize a run.

        :param dss_client: DSS client instance
        :param str project_key: Project identifier
        :param dict data: run data
        """
        self.dss_client = dss_client
        self.project_key = project_key
        self.data = data

    @property
    def id(self):
        """
        Unique ID of the run.
        :rtype: str
        """
        return self.data.get("id")

    @property
    def name(self):
        """
        Name of the run.
        :rtype: str
        """
        return self.data.get("name")

    @property
    def agent_review_id(self):
        """
        ID of the associated agent review.
        :rtype: str
        """
        return self.data.get("agentReviewId")

    @property
    def agent_id(self):
        """
        ID of the agent used in this run.
        :rtype: str
        """
        return self.data.get("agentSmartId")

    @property
    def agent_version(self):
        """
        Version of the agent used in this run.
        :rtype: str
        """
        return self.data.get("agentVersion")

    @property
    def status(self):
        """
        Status of the run.
        :rtype: str
        """
        return self.data.get("status")

    @property
    def error_message(self):
        """
        Error message of the run (nullable).
        :rtype: str
        """
        return self.data.get("errorMessage")

    @property
    def created_by(self):
        """
        Login of the user who created the result.
        :rtype: str
        """
        return self.data.get("createdBy")

    def get_raw(self):
        """
        Get the raw run data.
        :rtype: dict
        """
        return self.data

    def list_results(self, as_type='listitems'):
        """
        List all results produced by this run.

        :param str as_type: Type of objects to return. Can be 'listitems' (default) or 'objects'.
        :returns: List of results.
        :rtype: if as_type=listitems, each run as a :class:`DSSAgentReviewResultListItem`.
                if as_type=objects, each run is returned as a :class:`DSSAgentReviewResult`.
        """
        params = {"agentReviewId": self.agent_review_id, "runId": self.id}
        results = self.dss_client._perform_json(
            "GET", "/projects/%s/agent-reviews/results" % self.project_key, params=params
        )
        if as_type == 'listitems':
            return [DSSAgentReviewResultListItem(self.dss_client, self.project_key, result) for result in results]
        if as_type == 'objects':
            return [DSSAgentReviewResult(self.dss_client, self.project_key, result) for result in results]

    def get_result(self, result_id):
        """
        Get a specific result by its ID.

        :param str result_id: ID of the result to retrieve.
        :returns: The requested result.
        :rtype: :class:`DSSAgentReviewResult`
        """
        result = self.dss_client._perform_json(
            "GET", "/projects/%s/agent-reviews/results/%s" % (self.project_key, result_id)
        )
        return DSSAgentReviewResult(self.dss_client, self.project_key, result)

    def abort(self):
        """
        Abort the run.
        :returns: The terminated run.
        :rtype: :class:`DSSAgentReviewRun`
        """
        run = self.dss_client._perform_json(
            "POST", "/projects/%s/agent-reviews/reviews/%s/runs/%s/actions/abort" % (self.project_key, self.agent_review_id, self.id)
        )
        return DSSAgentReviewRun(self.dss_client, self.project_key, run)

    def list_traits(self):
        """
        Lists traits defined for this run.
        :return: List of traits.
        :rtype: list of :class:`DSSAgentReviewTrait`
        """
        traits = self.dss_client._perform_json(
            "GET", "/projects/%s/agent-reviews/reviews/%s/runs/%s/traits" % (self.project_key, self.agent_review_id, self.id)
        )
        return [DSSAgentReviewTrait(data) for data in traits]

    def rerun(self, wait=True, run_name=None):
        """
        Execute a new run with the same test selection.

        :param bool wait: If True, the call blocks until the run is finished. If False, it returns a future history handle. Defaults to True.
        :param str run_name: Optional name for the new run.
        :returns: The new run object if wait=True, or a future history handle if wait=False.
        :rtype: :class:`DSSAgentReviewRun` or :class:`dataikuapi.dss.future.DSSFutureWithHistory`
        """
        params = {
            "runId": self.id,
            "wait": wait,
            "runName": run_name
        }
        run_data = self.dss_client._perform_json(
            "POST", "/projects/%s/agent-reviews/reviews/%s/runs/actions/rerun" % (self.project_key, self.agent_review_id), params=params
        )
        if wait:
            return DSSAgentReviewRun(self.dss_client, self.project_key, run_data)
        else:
            # Name format must match AgentReviewRun.java getFutureHistoryKey()
            future_name = "agent-review-%s-%s-%s" % (self.project_key, self.id, run_data.get("id"))
            return DSSFutureWithHistory(self.dss_client, future_name, result_wrapper=lambda data: DSSAgentReviewRun(self.dss_client, self.project_key, data))

    def rename(self, new_name):
        """
        Rename the run.
        :param str new_name: The new name for the run.
        :returns: The updated run object.
        :rtype: :class:`DSSAgentReviewRun`
        """
        params = {
            "newName": new_name
        }
        self.dss_client._perform_json(
            "POST", "/projects/%s/agent-reviews/reviews/%s/runs/%s/actions/rename" % (self.project_key, self.agent_review_id, self.id), params=params
        )
        self.name = new_name

    def delete(self):
        """
        Delete this run.
        """
        self.dss_client._perform_empty(
            "DELETE", "/projects/%s/agent-reviews/reviews/%s/runs/%s" % (self.project_key, self.agent_review_id, self.id)
        )


class DSSAgentReviewRunListItem(dict):
    """
    An item in a list of agent review runs.

    .. important::

        Do not instantiate this class directly.
        Instances are returned by :meth:`DSSAgentReview.list_runs()`.
    """

    def __init__(self, dss_client, project_key, data):
        """
        Initialize an agent review run list item.

        :param dss_client: DSS client instance
        :param str project_key: Project identifier
        :param dict data: Run metadata
        """
        super().__init__(data)
        self.dss_client = dss_client
        self.project_key = project_key

    def to_agent_review_run(self):
        """
        Get a handle to interact with this agent review run.

        :returns: A handle on the agent review run.
        :rtype: :class:`DSSAgentReviewRun`
        """
        return DSSAgentReviewRun(self.dss_client, self.project_key, self)

    def delete(self):
        """
        Delete this run.
        """
        self.dss_client._perform_empty(
            "DELETE", "/projects/%s/agent-reviews/reviews/%s/runs/%s" % (self.project_key, self.agent_review_id, self.id)
        )

    @property
    def id(self):
        """
        Unique ID of the run.
        :rtype: str
        """
        return self.get("id")

    @property
    def name(self):
        """
        Name of the run.
        :rtype: str
        """
        return self.get("name")

    @property
    def agent_review_id(self):
        """
        ID of the associated agent review.
        :rtype: str
        """
        return self.get("agentReviewId")

    @property
    def agent_id(self):
        """
        ID of the agent used in this run.
        :rtype: str
        """
        return self.get("agentSmartId")

    @property
    def agent_version(self):
        """
        Version of the agent used in this run.
        :rtype: str
        """
        return self.get("agentVersion")


class DSSAgentReviewHumanReview(object):
    """
    Represents a human review (manual evaluation) of a test result.

    .. important::

        Do not instantiate this class directly.
        Instances are returned by :meth:`DSSAgentReviewResult.create_human_review()` or
        :meth:`DSSAgentReviewResult.list_human_reviews()`.
    """

    def __init__(self, dss_client, project_key, data):
        """
        Initialize a review of a test.

        :param dss_client: DSS client instance
        :param str project_key: Project identifier
        :param dict data: Review data
        """
        self.dss_client = dss_client
        self.project_key = project_key
        self.data = data

    @property
    def id(self):
        """
        Unique ID of the human review.
        :rtype: str
        """
        return self.data.get("id")

    @property
    def result_id(self):
        """
        ID of the result this human review refers to.
        :rtype: str
        """
        return self.data.get("resultId")

    @property
    def comment(self):
        """
        Text comment of the human review.
        :rtype: str
        """
        return self.data.get("comment")

    @comment.setter
    def comment(self, value):
        self.data["comment"] = value

    @property
    def like(self):
        """
        Like of the human review (True for Pass, False for Fail).
        :rtype: bool
        """
        return self.data.get("like")

    @like.setter
    def like(self, value):
        self.data["like"] = value

    @property
    def created_by(self):
        """
        Login of the user who created the review.
        :rtype: str
        """
        return self.data.get("createdBy")

    @property
    def last_modification_timestamp(self):
        """
        Timestamp of last modification (epoch millis).
        :rtype: int
        """
        return self.data.get("lastModifiedTimestamp")

    def get_raw(self):
        """
        Get the raw human review data.
        :rtype: dict
        """
        return self.data

    def save(self):
        """
        Save the human review.
        :returns: The updated human review.
        :rtype: :class:`DSSAgentReviewHumanReview`
        """
        result_dict = self.dss_client._perform_json(
            "PUT",
            "/projects/%s/agent-reviews/human-reviews/%s" % (self.project_key, self.id),
            body=self.get_raw()
        )
        return DSSAgentReviewHumanReview(self.dss_client, self.project_key, result_dict)

    def delete(self):
        """
        Delete this human review.
        """
        self.dss_client._perform_empty(
            "DELETE",
            "/projects/%s/agent-reviews/human-reviews/%s" % (self.project_key, self.id)
        )


class DSSAgentReviewHumanReviewListItem(dict):
    """
    An item in a list of result's human reviews.

    .. important::

        Do not instantiate this class directly.
        Instances are returned by :meth:`DSSAgentReviewResult.list_human_reviews()`.
    """

    def __init__(self, dss_client, project_key, data):
        """
        Initialize an human review list item.

        :param dss_client: DSS client instance
        :param str project_key: Project identifier
        :param dict data: Human review metadata
        """
        super().__init__(data)
        self.dss_client = dss_client
        self.project_key = project_key

    def delete(self):
        """
        Delete this human review.
        """
        self.dss_client._perform_empty(
            "DELETE",
            "/projects/%s/agent-reviews/human-reviews/%s" % (self.project_key, self.id)
        )

    @property
    def id(self):
        """
        Unique ID of the human review.
        :rtype: str
        """
        return self.get("id")

    @property
    def result_id(self):
        """
        ID of the result this human review refers to.
        :rtype: str
        """
        return self.get("resultId")

    @property
    def comment(self):
        """
        Text comment of the human review.
        :rtype: str
        """
        return self.get("comment")

    @property
    def like(self):
        """
        Like of the human review (True for Pass, False for Fail).
        :rtype: bool
        """
        return self.get("like")


class DSSAgentReviewTraitOverride(object):
    """
    Represents an trait override (manual evaluation) of a test result.

    .. important::

        Do not instantiate this class directly.
        Instances are returned by :meth:`DSSAgentReviewResult.create_trait_override()` or
        :meth:`DSSAgentReviewResult.list_trait_overrides()`.
    """

    def __init__(self, dss_client, project_key, data):
        """
        Initialize an trait override.

        :param dss_client: DSS client instance
        :param str project_key: Project identifier
        :param dict data: Trait override data
        """
        self.dss_client = dss_client
        self.project_key = project_key
        self.data = data

    @property
    def id(self):
        """
        Unique ID of the trait override.
        :rtype: str
        """
        return self.data.get("id")

    @property
    def result_id(self):
        """
        ID of the result this trait override refers to.
        :rtype: str
        """
        return self.data.get("resultId")

    @property
    def like(self):
        """
        Like of the trait override (True for Pass, False for Fail).
        :rtype: bool
        """
        return self.data.get("like")

    @like.setter
    def like(self, value):
        self.data["like"] = value

    @property
    def created_by(self):
        """
        Login of the user who created the trait override.
        :rtype: str
        """
        return self.data.get("createdBy")


    @property
    def creation_timestamp(self):
        """
        Timestamp of creation (epoch millis).
        :rtype: int
        """
        return self.data.get("creationTimestamp")

    @property
    def last_modification_timestamp(self):
        """
        Timestamp of last modification (epoch millis).
        :rtype: int
        """
        return self.data.get("lastModifiedTimestamp")

    @property
    def last_modified_by(self):
        """
        Login of the user who modified last.
        :rtype: str
        """
        return self.data.get("lastModifiedBy")

    def get_raw(self):
        """
        Get the raw trait override data.
        :rtype: dict
        """
        return self.data

    def save(self):
        """
        Save the trait override.
        :returns: The updated trait override.
        :rtype: :class:`DSSAgentReviewTraitOverride`
        """
        result_dict = self.dss_client._perform_json("PUT",
                                                    "/projects/%s/agent-reviews/trait-overrides/%s" % (self.project_key,self.id),
                                                    body=self.get_raw())
        return DSSAgentReviewTraitOverride(self.dss_client, self.project_key, result_dict)

    def delete(self):
        """
        Delete this trait override.
        """
        self.dss_client._perform_empty(
            "DELETE", "/projects/%s/agent-reviews/trait-overrides/%s" % (self.project_key, self.id)
        )


class DSSAgentReviewTraitOverrideListItem(dict):
    """
    An item in a list of agent review trait overrides.

    .. important::

        Do not instantiate this class directly.
        Instances are returned by :meth:`DSSAgentReviewResult.list_trait_overrides()`.
    """

    def __init__(self, dss_client, project_key, data):
        """
        Initialize an agent review trait override list item.

        :param dss_client: DSS client instance
        :param str project_key: Project identifier
        :param dict data: Trait override metadata
        """
        super().__init__(data)
        self.dss_client = dss_client
        self.project_key = project_key

    def delete(self):
        """
        Delete this trait override.
        """
        self.dss_client._perform_empty(
            "DELETE", "/projects/%s/agent-reviews/trait-overrides/%s" % (self.project_key, self.id)
        )

    @property
    def id(self):
        """
        Unique ID of the trait override.
        :rtype: str
        """
        return self.get("id")

    @property
    def result_id(self):
        """
        ID of the result this trait override refers to.
        :rtype: str
        """
        return self.get("resultId")

    @property
    def like(self):
        """
        Like/Dislike of the trait override (True for Pass, False for Fail).
        :rtype: bool
        """
        return self.get("like")


class DSSAgentReviewTraitOutcome(object):
    """
    Represents the result of an evaluation of a trait during an agent execution.
    """

    def __init__(self, dss_client, data):
        self.dss_client = dss_client
        self.data = data

    @property
    def id(self):
        """
        Unique ID of the trait result.
        :rtype: str
        """
        return self.data.get("id")

    @property
    def project_key(self):
        """
        Project key.
        :rtype: str
        """
        return self.data.get("projectKey")

    @property
    def justification(self):
        """
        Justification of the trait result.
        :rtype: str
        """
        return self.data.get("justification")

    @property
    def outcome(self):
        """
        Outcome of the trait result.
        :rtype: bool
        """
        return self.data.get("outcome")

    @property
    def result_id(self):
        """
        ID of the associated result.
        :rtype: str
        """
        return self.data.get("resultId")

    @property
    def trait_id(self):
        """
        ID of the trait.
        :rtype: str
        """
        return self.data.get("traitId")

    def get_raw(self):
        """
        Get the raw trait result data.
        :rtype: dict
        """
        return self.data

class DSSAgentReviewExecutionResult(object):
    """
    Represents the execution result of an agent review test.

    .. important::

        Do not instantiate this class directly.
        Instances are created internally and exposed through
        the :attr:`DSSAgentReviewResult.execution_results` attribute.
    """

    def __init__(self, dss_client, project_key, data):
        """
        Initialize an execution result.

        :param dss_client: DSS client instance
        :param str project_key: Project identifier
        :param dict data: Result data
        """
        self.dss_client = dss_client
        self.project_key = project_key
        self.data = data

    @property
    def id(self):
        """
        Unique ID of the execution result.
        :rtype: str
        """
        return self.data.get("id")

    @property
    def agent_review_id(self):
        """
        ID of the parent agent review.
        :rtype: str
        """
        return self.data.get("agentReviewId")

    @property
    def run_id(self):
        """
        ID of the run that produced this execution.
        :rtype: str
        """
        return self.data.get("runId")

    @property
    def test_id(self):
        """
        Test ID associated with this execution.
        :rtype: str
        """
        return self.data.get("testId")

    @property
    def result_id(self):
        """
        Result ID linking back to the review result.
        :rtype: str
        """
        return self.data.get("resultId")

    @property
    def answer(self):
        """
        Answer produced during this specific execution.
        :rtype: str
        """
        return self.data.get("answer")

    @property
    def error(self):
        """
        Error during this specific execution.
        :rtype: str
        """
        return self.data.get("error")

    @property
    def creation_timestamp(self):
        """
        Timestamp of creation (epoch millis).
        :rtype: int
        """
        return self.data.get("creationTimestamp")

    @property
    def trait_outcomes_per_trait_id(self):
        """
        Trait results for this execution, keyed by trait ID.

        :rtype: dict[str, :class:`DSSAgentReviewTraitOutcome`]
        """
        trait_map = self.data.get("traitOutcomePerTraitId", {})

        return {
            trait_id: DSSAgentReviewTraitOutcome(
                self.dss_client,
                trait_result
            )
            for trait_id, trait_result in trait_map.items()
        }

    def get_raw(self):
        """
        Get the raw data of this list object.
        :rtype: dict
        """
        return self.data



class DSSAgentReviewResult(object):
    """
    Represents the result of an execution of tests in a run.

    .. important::

        Do not instantiate this class directly.
        Instances are returned by :meth:`DSSAgentReviewRun.list_results()`.
    """

    def __init__(self, dss_client, project_key, data):
        """
        Initialize a result.

        :param dss_client: DSS client instance
        :param str project_key: Project identifier
        :param dict data: Result data
        """
        self.dss_client = dss_client
        self.project_key = project_key
        self.data = data

    @property
    def id(self):
        """
        Unique ID of the result.
        :rtype: str
        """
        return self.data.get("id")

    @property
    def test_id(self):
        """
        ID of the associated test.
        :rtype: str
        """
        return self.data.get("testId")

    @property
    def agent_review_id(self):
        """
        ID of the associated agent review.
        :rtype: str
        """
        return self.data.get("agentReviewId")

    @property
    def run_id(self):
        """
        ID of the associated run.
        :rtype: str
        """
        return self.data.get("runId")

    @property
    def query(self):
        """
        Query used in the test.
        :rtype: str
        """
        return self.data.get("query")

    @property
    def raw_query(self):
        """
        Raw query (e.g. including system prompt if available).
        :rtype: str
        """
        return self.data.get("rawQuery")

    @property
    def reference_answer(self):
        """
        Expected result of the query.
        :rtype: str
        """
        return self.data.get("referenceAnswer")

    @property
    def expectations(self):
        """
        Expectations on the agent answer.
        :rtype: str
        """
        return self.data.get("expectations")

    @property
    def tool_calls(self):
        """
        Tool calls performed by the agent
        :rtype: str
        """
        return self.data.get("toolCalls")

    @property
    def creation_timestamp(self):
        """
        Timestamp of creation (epoch millis).
        :rtype: int
        """
        return self.data.get("creationTimestamp")

    @property
    def agent_id(self):
        """
        ID of the associated agent.
        :rtype: str
        """
        return self.data.get("agentSmartId")

    @property
    def agent_version(self):
        """
        Version of the associated agent.
        :rtype: str
        """
        return self.data.get("agentVersion")

    @property
    def created_by(self):
        """
        Login of the user who created the result.
        :rtype: str
        """
        return self.data.get("createdBy")

    @property
    def created_by_display_name(self):
        """
        Display name of the user who created the result.
        :rtype: str
        """
        return self.data.get("createdByDisplayName")

    @property
    def status(self):
        """
        Status of the result.
        :rtype: str
        """
        return self.data.get("status")

    @property
    def human_reviews(self):
        """
        List of human reviews of this result.
        :rtype: list of :class:`DSSAgentReviewHumanReview`
        """
        return [DSSAgentReviewHumanReview(self.dss_client, self.project_key, data) for data in self.data.get("humanReviews", [])]

    @property
    def trait_status_per_trait_id(self):
        """
        Status of each trait for this result.
        :rtype: dict[str, str]
        """
        return self.data.get("traitStatusPerTraitId", {})

    @property
    def ai_status_per_trait_id(self):
        """
        AI-computed status of each trait for this result.
        :rtype: dict[str, str]
        """
        return self.data.get("aiStatusPerTraitId", {})

    @property
    def trait_status_justification_per_trait_id(self):
        """
        Justification for the status of each trait.
        :rtype: dict[str, str]
        """
        return self.data.get("traitStatusJustificationPerTraitId", {})

    @property
    def trait_overrides(self):
        """
        Trait overrides of human reviewers, grouped by trait ID.
        :rtype: dict[str, list of :class:`DSSAgentReviewTraitOverride`]
        """
        trait_overrides_map = self.data.get("traitOverridesPerTraitId", {})
        return {
            trait_id: [
                DSSAgentReviewTraitOverride(self.dss_client, self.project_key, trait_override)
                for trait_override in trait_overrides
            ]
            for trait_id, trait_overrides in trait_overrides_map.items()
        }

    @property
    def execution_results(self):
        """
        Execution results of the agent.
        :rtype: list of :class:`DSSAgentReviewExecutionResult`
        """
        return [DSSAgentReviewExecutionResult(self.dss_client, self.project_key, data) for data in self.data.get("executionResults", [])]


    def get_raw(self):
        """
        Get the raw result data.
        :rtype: dict
        """
        return self.data

    def get_trait_override(self, trait_override_id):
        """
        Get a specific trait override by its ID.

        :param str trait_override_id: ID of the trait override to retrieve.
        :returns: The requested trait override.
        :rtype: :class:`DSSAgentReviewTraitOverride`
        """
        trait_override = self.dss_client._perform_json(
            "GET", "/projects/%s/agent-reviews/trait-overrides/%s" % (self.project_key, trait_override_id)
        )
        return DSSAgentReviewTraitOverride(self.dss_client, self.project_key, trait_override)

    def create_trait_override(self, trait_id, like):
        """
        Create a trait override for this trait result.

        :param str trait_id: ID of the trait to override.
        :param bool like: True for like (Pass), False for dislike (Fail).
        :returns: The created trait override.
        :rtype: :class:`DSSAgentReviewTraitOverride`
        """
        body = {
            "traitId": trait_id,
            "projectKey": self.project_key,
            "resultId": self.id,
            "like": like
        }
        trait_override = self.dss_client._perform_json(
            "POST", "/projects/%s/agent-reviews/trait-overrides" % self.project_key, body=body
        )
        return DSSAgentReviewTraitOverride(self.dss_client, self.project_key, trait_override)

    def list_trait_overrides(self, as_type='listitems'):
        """
        List all trait overrides for this trait result.

        :param str as_type: Type of objects to return. Can be 'listitems' (default) or 'objects'.
        :returns: List of trait overrides.
        :rtype: if as_type=listitems, each trait override is returned as a :class:`DSSAgentReviewTraitOverrideListItem`.
                if as_type=objects, each trait override is returned as a :class:`DSSAgentReviewTraitOverride`.
        """
        params = {"resultId": self.id}
        trait_overrides = self.dss_client._perform_json(
            "GET", "/projects/%s/agent-reviews/trait-overrides" % self.project_key, params=params
        )
        if as_type == 'listitems':
            return [DSSAgentReviewTraitOverrideListItem(self.dss_client, self.project_key, trait_override) for trait_override in
                    trait_overrides]
        if as_type == 'objects':
            return [DSSAgentReviewTraitOverride(self.dss_client, self.project_key, trait_override) for trait_override in
                    trait_overrides]

    def get_human_review(self, human_review_id):
        """
        Get a specific human review by its ID.

        :param str human_review_id: ID of the human review to retrieve.
        :returns: The requested human review.
        :rtype: :class:`DSSAgentReviewHumanReview`
        """
        human_review = self.dss_client._perform_json(
            "GET", "/projects/%s/agent-reviews/human-reviews/%s" % (self.project_key, human_review_id)
        )
        return DSSAgentReviewHumanReview(self.dss_client, self.project_key, human_review)


    def create_human_review(self, comment=None, like=None):
        """
        Create a human review for this trait result.

        :param str comment: Text comment. Optional.
        :param bool like: Like of the review (True for Pass, False for Fail). Optional.
        :returns: The created human review.
        :rtype: :class:`DSSAgentReviewHumanReview`
        """
        body = {
            "projectKey": self.project_key,
            "agentReviewId": self.agent_review_id,
            "resultId": self.id,
            "comment": comment,
            "like": like,
            "runId": self.run_id
        }
        human_review = self.dss_client._perform_json(
            "POST", "/projects/%s/agent-reviews/human-reviews" % self.project_key, body=body
        )
        return DSSAgentReviewHumanReview(self.dss_client, self.project_key, human_review)


    def list_human_reviews(self, as_type='listitems'):
        """
        List all human reviews for this result.

        :param str as_type: Type of objects to return. Can be 'listitems' (default) or 'objects'.
        :returns: List of human reviews.
        :rtype: if as_type='listitems', each human review is returned as a :class:`DSSAgentReviewHumanReviewListItem`.
                if as_type='objects', each human review is returned as a :class:`DSSAgentReviewHumanReview`.
        """
        params = {"resultId": self.id}
        human_reviews = self.dss_client._perform_json(
            "GET", "/projects/%s/agent-reviews/human-reviews" % self.project_key, params=params
        )
        if as_type == 'listitems':
            return [DSSAgentReviewHumanReviewListItem(self.dss_client, self.project_key, hr) for hr in human_reviews]
        if as_type == 'objects':
            return [DSSAgentReviewHumanReview(self.dss_client, self.project_key, hr) for hr in human_reviews]


class DSSAgentReviewResultListItem(object):
    """
    An item in a list of agent review results.

    .. important::

        Do not instantiate this class directly.
        Instances are returned by :meth:`DSSAgentReviewRun.list_results()`.
    """

    def __init__(self, dss_client, project_key, data):
        """
        Initialize an agent review result list item.

        :param dss_client: DSS client instance
        :param str project_key: Project identifier
        :param dict data: Result metadata
        """
        self.dss_client = dss_client
        self.project_key = project_key
        self.data = data

    def to_agent_review_result(self):
        """
        Get a handle to interact with this agent review result.

        :returns: A handle on the agent review result.
        :rtype: :class:`DSSAgentReviewResult`
        """
        return DSSAgentReviewResult(self.dss_client, self.project_key, self.data)

    @property
    def id(self):
        """
        Unique ID of the result.
        :rtype: str
        """
        return self.data.get("id")

    @property
    def test_id(self):
        """
        ID of the associated test.
        :rtype: str
        """
        return self.data.get("testId")

    @property
    def agent_review_id(self):
        """
        ID of the associated agent review.
        :rtype: str
        """
        return self.data.get("agentReviewId")

    @property
    def run_id(self):
        """
        ID of the associated run.
        :rtype: str
        """
        return self.data.get("runId")

    @property
    def query(self):
        """
        Query used in the test.
        :rtype: str
        """
        return self.data.get("query")

    @property
    def raw_query(self):
        """
        Raw query (e.g. including system prompt if available).
        :rtype: str
        """
        return self.data.get("rawQuery")

    @property
    def reference_answer(self):
        """
        Expected result of the query.
        :rtype: str
        """
        return self.data.get("referenceAnswer")

    @property
    def expectations(self):
        """
        Expectations on the agent answer.
        :rtype: str
        """
        return self.data.get("expectations")

    @property
    def creation_timestamp(self):
        """
        Timestamp of creation (epoch millis).
        :rtype: int
        """
        return self.data.get("creationTimestamp")

    @property
    def agent_id(self):
        """
        ID of the associated agent.
        :rtype: str
        """
        return self.data.get("agentSmartId")

    @property
    def agent_version(self):
        """
        Version of the associated agent.
        :rtype: str
        """
        return self.data.get("agentVersion")

    @property
    def created_by(self):
        """
        Login of the user who created the result.
        :rtype: str
        """
        return self.data.get("createdBy")

    @property
    def created_by_display_name(self):
        """
        Display name of the user who created the result.
        :rtype: str
        """
        return self.data.get("createdByDisplayName")

    @property
    def status(self):
        """
        Status of the result.
        :rtype: str
        """
        return self.data.get("status")

    @property
    def trait_status_per_trait_id(self):
        """
        Status of each trait for this result.
        :rtype: dict[str, str]
        """
        return self.data.get("traitStatusPerTraitId", {})

    @property
    def ai_status_per_trait_id(self):
        """
        AI-computed status of each trait for this result.
        :rtype: dict[str, str]
        """
        return self.data.get("aiStatusPerTraitId", {})

    @property
    def trait_status_justification_per_trait_id(self):
        """
        Justification for the status of each trait.
        :rtype: dict[str, str]
        """
        return self.data.get("traitStatusJustificationPerTraitId", {})

    def get_raw(self):
        """
        Get the raw data of this list item.
        :rtype: dict
        """
        return self.data
