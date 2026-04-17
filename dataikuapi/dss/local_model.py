from .llm import DSSLLM
from requests import utils

class DSSLocalModelKernel(object):
    """
    Status of a single local model kernel.

    .. important::
        Do not instantiate this class directly, use :attr:`dataikuapi.dss.local_model.DSSLocalModelStatus.kernels` instead.
    """
    def __init__(self, client, connection_name, data):
        self.client = client
        self.connection_name = connection_name
        self._data = data or {}

    @property
    def kernel_id(self):
        return self._data.get("kernelId")

    @property
    def model_id(self):
        return self._data.get("modelId")

    @property
    def state(self):
        """
        Current state of the kernel.

        :returns: one of READY, STARTING, STOPPING, ERROR, STOPPED
        :rtype: string
        """
        return self._data.get("state", "")

    @property
    def metrics(self):
        """
        :returns: Kernel metrics if available (if kernel state is READY)
        :rtype: dict | None
        """
        return self._data.get("metrics")

    def get_log(self):
        """
        Fetch logs for this specific model kernel.

        :returns: Log payload
        :rtype: dict
        """
        return self.client._perform_json(
            "GET",
            "/connections/%s/local-models/kernels/%s/log-tail" % (self.connection_name, self.kernel_id),
            )

    def get_raw(self):
        """
        Get the raw API payload for this kernel status.

        :returns: Raw kernel status dictionary.
        :rtype: dict
        """
        return self._data

    def __repr__(self):
        return "<DSSLocalModelKernel model_id=%s kernel_id=%s state=%s>" % (self.model_id, self.kernel_id, self.state)


class DSSLocalModelStatus(object):
    """
    Status of a local model.

    .. important::
        Do not instantiate this class directly, use :meth:`dataikuapi.dss.local_model.DSSLocalModel.get_status` instead.
    """
    def __init__(self, client, connection_name, data):
        self.client = client
        self.connection_name = connection_name
        self._data = data or {}

    @property
    def model_id(self):
        return self._data.get("modelId")

    @property
    def kernels(self):
        """
        Per-kernel statuses for this model.

        :returns: List of kernel statuses.
        :rtype: list[DSSLocalModelKernel]
        """
        kernels = self._data.get("kernels", [])
        return [DSSLocalModelKernel(self.client, self.connection_name, kernel) for kernel in kernels]

    @property
    def state(self):
        """
        Aggregated model state.

        :returns: one of READY, STARTING, STOPPING, ERROR, STOPPED
        :rtype: string
        """
        return self._data.get("state", "")

    def get_raw(self):
        """
        Get the raw API payload for this model status.

        :returns: Raw model status dictionary.
        :rtype: dict
        """
        return self._data

    def __repr__(self):
        return "<DSSLocalModelStatus model_id=%s state=%s kernels=%s>" % (self.model_id, self.state, len(self.kernels))


class DSSLocalModel(object):
    """
    A local model defined in a DSS connection.

    .. important::
        Do not instantiate this class directly, use :meth:`dataikuapi.dss.admin.DSSConnection.get_local_model` instead.
    """

    def __init__(self, client, connection_name, model_id):
        self.client = client
        self.connection_name = connection_name
        self._model_id = model_id

    @property
    def model_id(self):
        return self._model_id

    def get_status(self):
        """
        Fetch the current model status.

        :returns: Model status wrapper.
        :rtype: DSSLocalModelStatus
        """
        data = self.client._perform_json(
            "GET",
            "/connections/%s/local-models/status/%s" % (self.connection_name, utils.quote(self.model_id, safe="")),
        )
        return DSSLocalModelStatus(self.client, self.connection_name, data)

    def wake_up(self):
        """
        Request wakeup of a model kernel.
        """
        return self.client._perform_empty(
            "POST",
            "/connections/%s/local-models/actions/wakeup/%s" % (self.connection_name, utils.quote(self.model_id, safe="")),
        )

    def shutdown(self, force=False):
        """
        Request shutdown of model kernels.

        :param boolean force: If True, force shutdown.
        """
        return self.client._perform_empty(
            "POST",
            "/connections/%s/local-models/actions/shutdown/%s" % (self.connection_name, utils.quote(self.model_id, safe="")),
            params={"force": force}
        )

    def as_llm(self, project_key=None):
        """
        Return this model as a DSS LLM handle.

        :param string project_key: Project key to bind the LLM handle to.
                                   If None, uses the client's default project.
        :returns: DSS LLM Handle for this local model.
        :rtype: DSSLLM
        """
        if project_key is None:
            project_key = self.client.get_default_project().project_key
        llm_id = "huggingfacelocal:%s:%s" % (self.connection_name, self.model_id)
        return DSSLLM(self.client, project_key, llm_id)

    def get_settings(self):
        """
        Fetch the model settings from the connection definition.

        :returns: Model settings wrapper.
        :rtype: DSSHFModelSettings
        """
        definition = self.client._perform_json(
            "GET", "/admin/connections/%s" % self.connection_name)
        if definition.get("type") != "HuggingFaceLocal":
            raise Exception("Connection %s is not a HuggingFaceLocal connection" % self.connection_name)
        params = definition.get("params", {})
        models = params.get("models", [])
        model_data = next((m for m in models if m.get("id") == self.model_id), None)
        if model_data is None:
            raise ValueError("Model '%s' not found in connection '%s'" % (self.model_id, self.connection_name))

        return DSSHFModelSettings(self.client, self.connection_name, model_data)

    def __repr__(self):
        return "<DSSLocalModel model_id=%s connection_name=%s>" % (self.model_id, self.connection_name)


class DSSHFModelSettings(object):
    """
    Settings of a HuggingFace local model.

    .. important::
        Do not instantiate this class directly, use :meth:`dataikuapi.dss.local_model.DSSLocalModel.get_settings` instead.
    """

    def __init__(self, client, connection_name, data):
        self.client = client
        self.connection_name = connection_name
        self._data = data

    @property
    def model_id(self):
        return self._data.get("id")

    def get_raw(self):
        """
        Get the raw model settings payload.

        :returns: Raw model settings dictionary.
        :rtype: dict
        """
        return self._data

    def __repr__(self):
        return "<DSSHFModelSettings model_id=%s>" % self.model_id