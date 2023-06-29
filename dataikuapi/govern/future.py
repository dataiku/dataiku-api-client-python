import time


class GovernFuture(object):
    """
    A future represents a long-running task on a Govern instance. It allows you to
    track the state of the task, retrieve its result when it is ready or abort it.

    Usage example:

    .. code-block:: python

        # In this example, 'client' is a GovernClient
        future = client.start_resync_users_from_supplier(['login'])

        # Waits until the user sync is complete
        sync_result = future.wait_for_result()

    .. note:: This class does not need to be instantiated directly. A :class:`dataikuapi.govern.future.GovernFuture` is usually returned by the API calls that are initiating long running-tasks.
    """

    def __init__(self, client, job_id, state=None, result_wrapper=lambda result: result):
        self.client = client
        self.job_id = job_id
        self.state = state
        self.state_is_peek = True
        self.result_wrapper = result_wrapper

    @staticmethod
    def from_resp(client, resp, result_wrapper=lambda result: result):
        """
        Creates a :class:`dataikuapi.govern.future.GovernFuture` from the response of an endpoint that initiated a long-running task.

        :param client: An api client to connect to the Govern backend
        :type client: :class:`dataikuapi.govern_client.GovernClient`
        :param resp: The response of the API call that initiated a long-running task.
        :type resp: dict
        :param result_wrapper: (optional) a function to apply to the result of the future, before it is returned by `get_result` or `wait_for_result` methods.
        :type result_wrapper: callable
        :return: :class:`dataikuapi.govern.future.GovernFuture`
        """
        return GovernFuture(client, resp.get('jobId', None), state=resp, result_wrapper=result_wrapper)

    @classmethod
    def get_result_wait_if_needed(cls, client, ret):
        """
        :meta private:
        """
        if 'jobId' in ret:
            future = GovernFuture(client, ret["jobId"], ret)
            future.wait_for_result()
            return future.get_result()
        else:
            return ret['result']

    def abort(self):
        """
        Aborts the long-running task.
        """
        self.client._perform_empty("DELETE", "/futures/%s" % self.job_id)

    def get_state(self):
        """
        Queries the state of the future, and fetches the result if it's ready.

        :return: the state of the future, including the result if it is ready.
        :rtype: dict
        """
        self.state = self.client._perform_json(
            "GET", "/futures/%s" % self.job_id, params={'peek': False})
        self.state_is_peek = False
        return self.state

    def peek_state(self):
        """
        Queries the state of the future, without fetching the result.

        :return: the state of the future
        :rtype: dict
        """
        self.state = self.client._perform_json(
            "GET", "/futures/%s" % self.job_id, params={'peek': True})
        self.state_is_peek = True
        return self.state

    def get_result(self):
        """
        Returns the future's result if it's ready.

        .. note:: if a custom result_wrapper was provided, it will be applied on the result that will be returned.

        :return: the result of the future
        :rtype: object
        :raises Exception: if the result is not ready (i.e. the task is still running, or it has failed)
        """
        if self.state is None or not self.state.get('hasResult', False) or self.state_is_peek:
            self.get_state()
        if self.state.get('hasResult', False):
            return self.result_wrapper(self.state.get('result', None))
        else:
            raise Exception("Result not ready")

    def has_result(self):
        """
        Checks whether the task is completed successfully and has a result.

        :return: True if the task has successfully returned a result, False otherwise
        :rtype: bool
        """
        if self.state is None or not self.state.get('hasResult', False):
            self.get_state()
        return self.state.get('hasResult', False)

    def wait_for_result(self):
        """
        Waits for the completion of the long-running task, and returns its result.

        .. note:: if a custom result_wrapper was provided, it will be applied on the result that will be returned.

        :return: the result of the future
        :rtype: object
        :raises Exception: if the task failed
        """
        if self.state is not None and self.state.get('hasResult', False):
            # no future created in backend, result already in the state
            return self.result_wrapper(self.state.get('result', None))
        if self.state is None or not self.state.get('hasResult', False) or self.state_is_peek:
            self.get_state()
        while not self.state.get('hasResult', False):
            time.sleep(5)
            self.get_state()
        if self.state.get('hasResult', False):
            return self.result_wrapper(self.state.get('result', None))
        else:
            raise Exception("No result")
