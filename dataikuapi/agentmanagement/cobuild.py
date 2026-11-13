"""Cobuild conversations for Agent Management, using the shared DSS message and plan types."""

from dataikuapi.dss.cobuild import (
    CobuildAssistantResponse, CobuildUserMessage, CobuildMessage, CobuildConversationMode,
    CobuildPlan, CobuildPlanStatus, CobuildPlanMilestone, CobuildPlanMilestoneStatus, CobuildPlanImplementationNotes,
)
from ._utils import dku_quote_fn


class CobuildConversation(object):
    """
    A handle to a Cobuild conversation in Agent Management.

    Create a conversation with
    :meth:`dataikuapi.agentmanagement_client.AgentManagementClient.new_cobuild_conversation`.
    All exchanges made through this handle are accumulated in :attr:`messages`.

    For example::

        conversation = client.new_cobuild_conversation()
        response = conversation.send_message("List the agents in my estate")
        print(response.message)

    Send messages in :attr:`CobuildConversationMode.PLAN` mode to draft or revise a plan,
    then call :meth:`approve_plan` to execute it. Call :meth:`detach_plan` before leaving
    plan mode with a draft, or entering plan mode while an active plan is attached.
    """

    def __init__(self, client, conversation_id):
        self.client = client
        self.conversation_id = conversation_id
        self._messages = []
        self._pending_confirmation_id = None
        self._pending_question_id = None

    @property
    def messages(self):
        """
        All user messages and assistant responses exchanged through this handle, in order.

        :rtype: list of :class:`CobuildUserMessage` or :class:`CobuildAssistantResponse`
        """
        return list(self._messages)

    def _path(self, suffix):
        return "/agent-management/cobuild/conversations/%s/%s" % (dku_quote_fn(self.conversation_id, safe=""), suffix)

    def _record_response(self, raw):
        response = CobuildAssistantResponse(raw)
        self._pending_confirmation_id = raw["confirmationId"] if response.is_confirmation_request else None
        self._pending_question_id = raw["questionId"] if response.is_question_request else None
        self._messages.append(response)
        return response

    def send_message(self, message, allow_edit=False, conversation_mode=CobuildConversationMode.BUILD, intelligence_level=None):
        """
        Send a message and wait for the assistant's response.

        :param str message: the message to send
        :param bool allow_edit: allow Cobuild to create and edit Agent Management objects
            for this turn. Missing tool permissions are returned as an error response.
        :param CobuildConversationMode conversation_mode: ``BUILD`` (the default) for normal
            or plan-execution messages, or ``PLAN`` to draft or revise a plan
        :param str intelligence_level: optional ``LIGHT``, ``MEDIUM``, ``HIGH``, or
            ``VERY_HIGH``. ``None`` defaults to ``MEDIUM``.
        :rtype: :class:`CobuildAssistantResponse`
        """
        if not isinstance(conversation_mode, CobuildConversationMode):
            raise ValueError("conversation_mode must be a CobuildConversationMode, got %r" % conversation_mode)
        self._messages.append(CobuildUserMessage({
            "type": "request", "message": message, "conversation_mode": conversation_mode.value,
        }))
        raw = self.client._perform_json("POST", self._path("messages"), body={
            "message": message, "selectedObjects": [], "allowEditProject": allow_edit,
            "conversationMode": conversation_mode.value, "intelligenceLevel": intelligence_level,
        })
        return self._record_response(raw)

    def approve_plan(self, allow_edit=False, intelligence_level=None):
        """
        Approve the current draft plan and wait for its execution response.

        :param bool allow_edit: allow Cobuild to create and edit Agent Management objects
            for this turn. Pass it again on subsequent turns if execution pauses.
        :param str intelligence_level: optional ``LIGHT``, ``MEDIUM``, ``HIGH``, or
            ``VERY_HIGH``. ``None`` defaults to ``MEDIUM``.
        :rtype: :class:`CobuildAssistantResponse`
        """
        raw = self.client._perform_json("POST", self._path("plan/approve"), body={
            "allowEditProject": allow_edit, "intelligenceLevel": intelligence_level,
        })
        return self._record_response(raw)

    def detach_plan(self):
        """Detach the current draft, active, or completed plan and return to build mode."""
        return self.client._perform_empty("POST", self._path("plan/discard"))

    def answer_confirmation(self, choice, options=None):
        """
        Answer a pending confirmation request and wait for the next response.

        Call this when :attr:`CobuildAssistantResponse.is_confirmation_request` is true.
        Inspect :attr:`CobuildAssistantResponse.objects_to_delete` and
        :attr:`CobuildAssistantResponse.deletion_impacts` before approving.

        :param str choice: ``APPROVE`` to proceed or ``CANCEL`` to abort
        :param list options: optional per-object deletion options, as in
            :meth:`dataikuapi.dss.cobuild.DSSCobuildConversation.answer_confirmation`
        :rtype: :class:`CobuildAssistantResponse`
        """
        if choice not in ("APPROVE", "CANCEL"):
            raise ValueError("choice must be 'APPROVE' or 'CANCEL', got %r" % choice)
        if self._pending_confirmation_id is None:
            raise ValueError("No pending confirmation request. Call send_message first and check is_confirmation_request.")
        confirmation_id = self._pending_confirmation_id
        self._messages.append(CobuildUserMessage({"type": "delete_confirmation_response", "message": choice}))
        body = {"choice": choice}
        if options is not None:
            body["options"] = options
        raw = self.client._perform_json("POST", self._path("confirmation/" + dku_quote_fn(confirmation_id, safe="")), body=body)
        return self._record_response(raw)

    def answer_question(self, answers=None, rejected=False, used_custom_answer=False):
        """
        Answer a pending question request and wait for the next response.

        Call this when :attr:`CobuildAssistantResponse.is_question_request` is true.

        :param list[str] answers: selected or free-text answers. Defaults to ``[]``.
        :param bool rejected: decline answering the question; use an empty answer list
        :param bool used_custom_answer: whether an answer came from custom free-text input
        :rtype: :class:`CobuildAssistantResponse`
        """
        if answers is None:
            answers = []
        if not isinstance(answers, list) or any(not isinstance(answer, str) for answer in answers):
            raise ValueError("answers must be a list of strings")
        if self._pending_question_id is None:
            raise ValueError("No pending question request. Call send_message first and check is_question_request.")
        question_id = self._pending_question_id
        self._messages.append(CobuildUserMessage({
            "type": "ask_question_to_user_response", "message": None if rejected else ", ".join(answers),
        }))
        raw = self.client._perform_json("POST", self._path("question/" + dku_quote_fn(question_id, safe="")), body={
            "answers": answers, "rejected": rejected, "usedCustomAnswer": used_custom_answer, "selectedObjects": [],
        })
        return self._record_response(raw)
