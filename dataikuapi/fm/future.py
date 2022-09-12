import sys, time


class FMFuture(object):
    """
    A future on the DSS instance
    """

    def __init__(
        self, client, job_id, state=None, result_wrapper=lambda result: result
    ):
        self.client = client
        self.job_id = job_id
        self.state = state
        self.state_is_peek = True
        self.result_wrapper = result_wrapper

    @staticmethod
    def from_resp(client, resp, result_wrapper=lambda result: result):
        """
        Creates a DSSFuture from a parsed JSON response

        :rtype: :class:`dataikuapi.fm.future.FMFuture`
        """
        return FMFuture(
            client, resp.get("jobId", None), state=resp, result_wrapper=result_wrapper
        )

    @classmethod
    def get_result_wait_if_needed(cls, client, ret):
        if "jobId" in ret:
            future = FMFuture(client, ret["jobId"], ret)
            future.wait_for_result()
            return future.get_result()
        else:
            return ret["result"]

    def abort(self):
        """
        Abort the future
        """
        return self.client._perform_tenant_empty("DELETE", "/futures/%s" % self.job_id)

    def get_state(self):
        """
        Get the status of the future, and its result if it's ready
        """
        self.state = self.client._perform_tenant_json(
            "GET", "/futures/%s" % self.job_id, params={"peek": False}
        )
        self.state_is_peek = False
        return self.state

    def peek_state(self):
        """
        Get the status of the future, and its result if it's ready
        """
        self.state = self.client._perform_tenant_json(
            "GET", "/futures/%s" % self.job_id, params={"peek": True}
        )
        self.state_is_peek = True
        return self.state

    def get_result(self):
        """
        Get the future result if it's ready, raises an Exception otherwise
        """
        if (
            self.state is None
            or not self.state.get("hasResult", False)
            or self.state_is_peek
        ):
            self.get_state()
        if self.state.get("hasResult", False):
            return self.result_wrapper(self.state.get("result", None))
        else:
            raise Exception("Result not ready")

    def has_result(self):
        """
        Checks whether the future has a result ready
        """
        if self.state is None or not self.state.get("hasResult", False):
            self.get_state()
        return self.state.get("hasResult", False)

    def wait_for_result(self):
        """
        Wait and get the future result
        """
        if self.state.get("hasResult", False):
            return self.result_wrapper(self.state.get("result", None))
        if (
            self.state is None
            or not self.state.get("hasResult", False)
            or self.state_is_peek
        ):
            self.get_state()
        while not self.state.get("hasResult", False):
            time.sleep(5)
            self.get_state()
        if self.state.get("hasResult", False):
            return self.result_wrapper(self.state.get("result", None))
        else:
            raise Exception("No result")
