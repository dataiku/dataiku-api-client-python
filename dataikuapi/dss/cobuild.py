from dataikuapi.dss.dataset import DSSDataset
from dataikuapi.dss.evaluationstore import DSSEvaluationStore
from dataikuapi.dss.knowledgebank import DSSKnowledgeBank
from dataikuapi.dss.labeling_task import DSSLabelingTask
from dataikuapi.dss.managedfolder import DSSManagedFolder
from dataikuapi.dss.recipe import DSSRecipe
from dataikuapi.dss.savedmodel import DSSSavedModel
from dataikuapi.dss.streaming_endpoint import DSSStreamingEndpoint


class CobuildMessage(object):
    def __init__(self, raw):
        self._raw = raw

    @property
    def message(self):
        """
        The text content of the response.

        :rtype: str or None
        """
        return self._raw.get("message")


class CobuildAssistantResponse(CobuildMessage):
    """
    A response from the Cobuild AI assistant.

    .. important::
        Do not create this class directly, it is returned by :meth:`DSSCobuildConversation.send_message`
        :meth:`DSSCobuildConversation.answer_confirmation`, and
        :meth:`DSSCobuildConversation.answer_question`.
    """

    @property
    def role(self):
        """
        Role of the message sender ("user" or "assistant")

        :rtype: str
        """
        return "assistant"

    @property
    def type(self):
        """
        Type of the response: ``"assistant_message"``, ``"delete_confirmation_request"``,
        ``"ask_question_to_user_request"``, or ``"error"``.

        - ``"assistant_message"``: the assistant has completed its turn; the conversation is idle.
        - ``"delete_confirmation_request"``: the assistant is requesting confirmation before
          deleting objects. Call :meth:`DSSCobuildConversation.answer_confirmation`
          with a choice of ``"APPROVE"`` or ``"CANCEL"`` to continue.
        - ``"ask_question_to_user_request"``: the assistant is requesting an explicit answer before it can
          continue. Call :meth:`DSSCobuildConversation.answer_question` to continue.
        - ``"error"``: an error occurred while processing the Cobuild turn. In the public API,
          missing tool permissions are reported through this error response too.

        :rtype: str
        """
        return self._raw.get("type")

    @property
    def is_question(self):
        """
        DEPRECATED ... DEPRECATED ... DEPRECATED ... DEPRECATED
        Whether the assistant is asking the user a question. If ``True``, call
        :meth:`DSSCobuildConversation.send_message` again with the answer to continue.

        :rtype: bool
        """
        return False

    @property
    def is_confirmation_request(self):
        """
        Whether the assistant is requesting confirmation before deleting objects
        or doing other operations requiring confirmation.
        If ``True``, call :meth:`DSSCobuildConversation.answer_confirmation` with a choice of
        ``"APPROVE"`` or ``"CANCEL"`` to continue.
        If the confirmation is about a deletion, inspect :attr:`objects_to_delete`
        and :attr:`deletion_impacts` for details.

        :rtype: bool
        """
        return self.type == "delete_confirmation_request"

    @property
    def is_question_request(self):
        """
        Whether the assistant is requesting an explicit answer before continuing.
        If ``True``, call :meth:`DSSCobuildConversation.answer_question`.

        :rtype: bool
        """
        return self.type == "ask_question_to_user_request"

    @property
    def is_error(self):
        """
        Whether the response represents an error.

        :rtype: bool
        """
        return self._raw.get("error", False)

    @property
    def objects_to_delete(self):
        """
        For ``"delete_confirmation_request"`` responses: the list of objects that the assistant
        is requesting permission to delete (or unshare). Each entry is a dict with fields
        ``projectKey``, ``type``, ``id``, and ``displayName``.

        ``None`` for other response types.

        :rtype: list of dict or None
        """
        return self._raw.get("objectsToDelete")

    @property
    def deletion_impacts(self):
        """
        For ``"delete_confirmation_request"`` responses: a dict describing the cascading effects
        of the requested deletion (recipes that would be deleted, datasets left unchanged, etc.).

        ``None`` for other response types.

        :rtype: dict or None
        """
        return self._raw.get("deletionImpacts")

    @property
    def question_id(self):
        """
        For ``"ask_question_to_user_request"`` responses: the identifier of the pending question.

        ``None`` for other response types.

        :rtype: str or None
        """
        return self._raw.get("questionId")

    @property
    def title(self):
        """
        For ``"ask_question_to_user_request"`` responses: the short question shown to the user.

        ``None`` for other response types.

        :rtype: str or None
        """
        return self._raw.get("title")

    @property
    def predefined_answers(self):
        """
        For ``"ask_question_to_user_request"`` responses: the list of predefined answers proposed by Cobuild.

        ``None`` for other response types.

        :rtype: list[str] or None
        """
        return self._raw.get("predefinedAnswers")

    @property
    def allow_custom_answer(self):
        """
        For ``"ask_question_to_user_request"`` responses: whether a custom free-text answer is allowed.

        ``None`` for other response types.

        :rtype: bool or None
        """
        return self._raw.get("allowCustomAnswer")

    @property
    def allow_multiple_answers(self):
        """
        For ``"ask_question_to_user_request"`` responses: whether multiple answers can be selected.

        ``None`` for other response types.

        :rtype: bool or None
        """
        return self._raw.get("allowMultipleAnswers")

    @property
    def default_answer_set(self):
        """
        For ``"ask_question_to_user_request"`` responses: whether Cobuild suggested a default answer.

        ``None`` for other response types.

        :rtype: bool or None
        """
        return self._raw.get("selectFirstAnswerByDefault")

    def __repr__(self):
        return "CobuildAssistantResponse(type=%r, message=%r)" % (self.type, self.message)


class CobuildUserMessage(CobuildMessage):
    """
    A message sent to Cobuild AI assistant by the user.

    .. important::
        Do not create this class directly, it is automatically created when using :meth:`dataikuapi.dss.project.DSSProject.new_cobuild_conversation`,
        :meth:`DSSCobuildConversation.send_message`, and
        :meth:`DSSCobuildConversation.answer_confirmation`, and
        :meth:`DSSCobuildConversation.answer_question`.
    """

    @property
    def role(self):
        """
        Role of the message sender ("user" or "assistant")

        :rtype: str
        """
        return "user"

    @property
    def type(self):
        """
        Type of the message: ``"request"``, ``"delete_confirmation_response"``, or
        ``"ask_question_to_user_response"``.

        - ``"request"``: a normal message sent to cobuild.
        - ``"delete_confirmation_response"``: user response when cobuild requests confirmation before deleting objects
        - ``"ask_question_to_user_response"``: user response when cobuild requests an explicit answer

        :rtype: str
        """
        return self._raw.get("type", "request")

    @property
    def is_confirmation_response(self):
        """
        Whether this message is the answer for assistant requesting confirmation before deleting objects

        :rtype: bool
        """
        return self.type == "delete_confirmation_response"

    @property
    def is_question_response(self):
        """
        Whether this message is the answer for assistant requesting an explicit answer.

        :rtype: bool
        """
        return self.type == "ask_question_to_user_response"

    def __repr__(self):
        return "CobuildUserMessage(type=%r, message=%r)" % (self.type, self.message)

def _DSS_objects_to_selected(project_key, objects):
    return [_DSS_object_to_selected(project_key, object) for object in objects]

def _DSS_object_to_selected(project_key, object):
    prefix = "" if project_key == object.project_key else object.project_key + "."

    if isinstance(object, DSSDataset):
        return { "type": "DATASET", "id": prefix + object.id}
    if isinstance(object, DSSRecipe):
        return { "type": "RECIPE", "id": prefix + object.id}
    if isinstance(object, DSSManagedFolder):
        return { "type": "MANAGED_FOLDER", "id": prefix + object.id}
    if isinstance(object, DSSSavedModel):
        return { "type": "SAVED_MODEL", "id": prefix + object.id}
    if isinstance(object, DSSStreamingEndpoint):
        return { "type": "STREAMING_ENDPOINT", "id": prefix + object.id}
    if isinstance(object, DSSLabelingTask):
        return { "type": "LABELING_TASK", "id": prefix + object.id}
    if isinstance(object, DSSKnowledgeBank):
        return { "type": "RETRIEVABLE_KNOWLEDGE", "id": prefix + object.id}
    if isinstance(object, DSSEvaluationStore):
        return { "type": "MODEL_EVALUATION_STORE", "id": prefix + object.id}
    else:
        raise ValueError("Unsupported object type")


class DSSCobuildConversation(object):
    """
    A handle to a conversation with Cobuild AI assistant.

    .. important::
        Do not create this class directly, instead use
        :meth:`dataikuapi.dss.project.DSSProject.new_cobuild_conversation`.

    The :attr:`messages` property accumulates all exchanges made through this handle (user inputs
    and assistant responses).

    A typical interaction::

        conv = project.new_cobuild_conversation()
        response = conv.send_message("List the datasets in this project")
        print(response.message)

        conv.send_message("Now filter the Orders dataset to keep only orders with an amount > 1000")
        print(conv.messages[-1].message)

    When the assistant needs to delete objects, it first asks for confirmation::

        response = conv.send_message("Delete the Orders dataset")
        if response.is_confirmation_request:
            print("Objects to delete:", response.objects_to_delete)
            response = conv.answer_confirmation("APPROVE")
            print(response.message)

    When the assistant needs an explicit answer, it asks a question::

        response = conv.send_message("Use the best date column for sorting")
        if response.is_question_request:
            print("Question:", response.title)
            print("Choices:", response.predefined_answers)
            print("Allow custom answer:", response.allow_custom_answer)
            response = conv.answer_question(
                answers=["OrderDate"],
                rejected=False,
                used_custom_answer=False
            )
            print(response.message)

    You can also decline answering a question::

        response = conv.send_message("Pick the dataset to build")
        if response.is_question_request:
            response = conv.answer_question(
                answers=[],
                rejected=True,
                used_custom_answer=False
            )
            print(response.message)

    If a tool requires edit permission, pass ``allow_edit_project=True`` to
    :meth:`send_message` to allow Cobuild to create and edit objects for that message.
    """

    def __init__(self, client, project_key, conversation_id, selected_objects=None):
        self.client = client
        self.project_key = project_key
        self.conversation_id = conversation_id
        self._messages = []
        self._pending_confirmation_id = None
        self._pending_question_id = None
        self._selected_objects = selected_objects

    @property
    def messages(self):
        """
        All messages exchanged during this conversation, in order.

        User message entries are :class:`CobuildUserMessage`.

        Assistant message entries are :class:`CobuildAssistantResponse`.

        :rtype: list of :class:`CobuildAssistantResponse` or :class:`CobuildUserMessage`
        """
        return list(self._messages)

    def send_message(self, message, selected_objects=None, allow_edit_project=False):
        """
        Send a message to the assistant and wait for its response.

        The message and assistant response are appended to :attr:`messages`.

        :param str message: the message to send
        :param selected_objects: object selection the assistant should focus on. It is reused for any subsequent message, unless overwritten
        :type selected_objects: list[:class:`.DSSDataset`, :class:`.DSSRecipe`, :class:`.DSSLabelingTask`, :class:`.DSSManagedFolder`, :class:`.DSSSavedModel`, :class:`.DSSKnowledgeBank`, :class:`.DSSModelEvaluationStore` or :class:`.DSSStreamingEndpoint`]
        :param bool allow_edit_project: whether to allow Cobuild to create and edit everything
            needed in this project to follow this message. This permission applies only to this
            message.

        :returns: the assistant's response
        :rtype: :class:`CobuildAssistantResponse`
        """
        if selected_objects is not None:
            self._selected_objects = _DSS_objects_to_selected(self.project_key, selected_objects)

        self._messages.append(CobuildUserMessage({"type": "request", "message": message, "selected_objects": self._selected_objects}))
        raw = self.client._perform_json(
            "POST",
            "/projects/%s/cobuild/conversations/%s/messages" % (self.project_key, self.conversation_id),
            body={
                "message": message,
                "selectedObjects": self._selected_objects or [],
                "allowEditProject": allow_edit_project,
            },
        )
        response = CobuildAssistantResponse(raw)
        self._pending_confirmation_id = raw["confirmationId"] if response.is_confirmation_request else None
        self._pending_question_id = raw["questionId"] if response.is_question_request else None
        self._messages.append(response)
        return response

    def answer_confirmation(self, choice, options=None):
        """
        Answer a pending confirmation request and wait for the assistant's next response.

        Call this after receiving a response with :attr:`~CobuildAssistantResponse.is_confirmation_request`
        set to ``True``.

        The choice and assistant response are appended to :attr:`messages`.

        :param str choice: ``"APPROVE"`` to proceed with the operation, or ``"CANCEL"`` to abort it
        :param list options: optional list of per-object deletion options (advanced use, for delete
            confirmations only). Each entry is a dict with ``projectKey``, ``type``, ``id``, and an
            ``options`` dict containing ``dropData``, ``dropMetastoreTable``, and
            ``deleteOrphanInsights`` booleans. When omitted, all options default to ``False``
            (data is not dropped, metastore tables are not dropped, orphan insights are not deleted).

        :returns: the assistant's response after the confirmation
        :rtype: :class:`CobuildAssistantResponse`
        """
        if choice not in ("APPROVE", "CANCEL"):
            raise ValueError("choice must be 'APPROVE' or 'CANCEL', got %r" % choice)
        if self._pending_confirmation_id is None:
            raise ValueError("No pending confirmation request. Call send_message first and check is_confirmation_request.")

        confirmation_id = self._pending_confirmation_id
        self._pending_confirmation_id = None
        self._messages.append(CobuildUserMessage({"type": "delete_confirmation_response", "message": choice}))
        body = {"choice": choice}
        if options is not None:
            body["options"] = options
        raw = self.client._perform_json(
            "POST",
            "/projects/%s/cobuild/conversations/%s/confirmation/%s" % (self.project_key, self.conversation_id, confirmation_id),
            body=body,
        )
        response = CobuildAssistantResponse(raw)
        self._pending_confirmation_id = raw["confirmationId"] if response.is_confirmation_request else None
        self._pending_question_id = raw["questionId"] if response.is_question_request else None
        self._messages.append(response)
        return response

    def answer_question(self, answers=None, rejected=False, used_custom_answer=False):
        """
        Answer a pending question request and wait for the assistant's next response.

        Call this after receiving a response with :attr:`~CobuildAssistantResponse.is_question_request`
        set to ``True``.

        The answer and assistant response are appended to :attr:`messages`.

        :param list[str] answers: answers selected or entered by the user. Use an empty list when
            ``rejected=True``. Defaults to ``[]``.
        :param bool rejected: whether to decline answering the question
        :param bool used_custom_answer: whether one of the answers came from the custom free-text input

        :returns: the assistant's response after the question answer
        :rtype: :class:`CobuildAssistantResponse`
        """
        if answers is None:
            answers = []
        if not isinstance(answers, list):
            raise ValueError("answers must be a list of strings")
        if self._pending_question_id is None:
            raise ValueError("No pending question request. Call send_message first and check is_question_request.")

        question_id = self._pending_question_id
        self._pending_question_id = None
        self._messages.append(CobuildUserMessage({
            "type": "ask_question_to_user_response",
            "message": None if rejected else ", ".join(answers),
        }))
        raw = self.client._perform_json(
            "POST",
            "/projects/%s/cobuild/conversations/%s/question/%s" % (self.project_key, self.conversation_id, question_id),
            body={
                "rejected": rejected,
                "answers": answers,
                "usedCustomAnswer": used_custom_answer,
            },
        )
        response = CobuildAssistantResponse(raw)
        self._pending_confirmation_id = raw["confirmationId"] if response.is_confirmation_request else None
        self._pending_question_id = raw["questionId"] if response.is_question_request else None
        self._messages.append(response)
        return response
