from requests import utils

from .utils import DSSTaggableObjectListItem, DSSTaggableObjectSettings


class DSSAgentSkillListItem(DSSTaggableObjectListItem):
    """
    .. important::
        Do not instantiate this class directly, instead use :meth:`dataikuapi.dss.project.DSSProject.list_agent_skills`.
    """

    def __init__(self, client, project_key, data):
        super(DSSAgentSkillListItem, self).__init__(data)
        self.client = client
        self.project_key = data.get("projectKey", project_key)

    def to_agent_skill(self):
        """
        Convert the current item.

        :rtype: :class:`dataikuapi.dss.agent_skill.DSSAgentSkill`
        """
        return DSSAgentSkill(self.client, self.project_key, self._data["id"])

    @property
    def id(self):
        """
        :returns: The id of the skill.
        :rtype: string
        """
        return self._data["id"]

    @property
    def name(self):
        """
        :returns: The name of the skill.
        :rtype: string
        """
        return self._data.get("name")


class DSSAgentSkill(object):
    """
    .. important::
        Do not instantiate this class directly, instead use :meth:`dataikuapi.dss.project.DSSProject.get_agent_skill`.
    """

    def __init__(self, client, project_key, skill_id):
        self.client = client
        self.project_key = project_key
        self.skill_id = skill_id

    @property
    def id(self):
        """
        :returns: The id of the skill.
        :rtype: string
        """
        return self.skill_id

    def get_settings(self):
        """
        Get the DSS metadata settings of the agent skill.

        The parsed ``SKILL.md`` fields are available through
        :meth:`get_skill_content` and the raw file through :meth:`get_file`.

        :return: a handle on the skill settings
        :rtype: :class:`dataikuapi.dss.agent_skill.DSSAgentSkillSettings`
        """
        settings = self.client._perform_json(
            "GET",
            "/projects/%s/agents/skills/%s" % (self.project_key, self.id),
        )
        return DSSAgentSkillSettings(self, settings)

    def get_skill_content(self):
        """
        Get the parsed contents of ``SKILL.md``.

        :returns: A dictionary containing ``name``, ``description``,
            ``metadata``, and ``instructions``.
        :rtype: dict
        """
        return self.client._perform_json(
            "GET",
            "/projects/%s/agents/skills/%s/content"
            % (self.project_key, self.id),
        )

    def delete(self):
        """
        Delete the agent skill.
        """
        return self.client._perform_empty("DELETE", "/projects/%s/agents/skills/%s" % (self.project_key, self.id))

    def list_resources(self):
        """
        List the files and folders attached to this skill as a recursive tree.

        :rtype: list[dict]
        """
        return self.client._perform_json(
            "GET",
            "/projects/%s/agents/skills/%s/resources/contents" % (self.project_key, self.id),
        )

    def get_file(self, path):
        """
        Get a file's contents.

        :param str path: Root-relative path of the file to download
        :rtype: :class:`requests.models.Response`
        """
        return self.client._perform_raw(
            "GET",
            "/projects/%s/agents/skills/%s/resources/contents/%s"
            % (self.project_key, self.id, utils.quote(path)),
        )

    def get_file_details(self, path):
        """
        Get a file's metadata without its content.

        :param str path: Root-relative path of the file
        :rtype: dict
        """
        return self.client._perform_json(
            "GET",
            "/projects/%s/agents/skills/%s/resources/details/%s"
            % (self.project_key, self.id, utils.quote(path)),
        )

    def put_file(self, path, data):
        """
        Create or overwrite a file.

        Strings are encoded as UTF-8 and bytes are stored unchanged. Parent
        folders must already exist. Replacing the root ``SKILL.md`` validates
        the supplied content and rejects an invalid skill file.

        :param str path: Root-relative path of the file
        :param data: String, bytes, or file-like content
        :rtype: dict
        """
        if isinstance(data, str):
            data = data.encode("utf-8")
        elif not isinstance(data, bytes) and not hasattr(data, "read"):
            raise TypeError("data must be a string, bytes, or file-like object")
        return self.client._perform_json(
            "PUT",
            "/projects/%s/agents/skills/%s/resources/contents/%s"
            % (self.project_key, self.id, utils.quote(path)),
            files={"file": (path.rsplit("/", 1)[-1], data)},
        )

    def rename_resource(self, path, new_name):
        """
        Rename a resource.

        :param str path: Root-relative path of the existing resource
        :param str new_name: New file name, without a folder path
        :rtype: str
        """
        return self.client._perform_raw(
            "POST",
            "/projects/%s/agents/skills/%s/resources/contents-actions/rename"
            % (self.project_key, self.id),
            body={"oldPath": path, "newName": new_name},
        ).text

    def move_resource(self, path, new_path):
        """
        Move a resource to a destination folder.

        :param str path: Root-relative path of the existing resource
        :param str new_path: Root-relative path of the destination folder, or an empty string for the skill root
        :rtype: str
        """
        return self.client._perform_raw(
            "POST",
            "/projects/%s/agents/skills/%s/resources/contents-actions/move"
            % (self.project_key, self.id),
            body={"oldPath": path, "newPath": new_path},
        ).text

    def create_folder(self, path):
        """
        Create a resource folder in the skill.

        Missing parent folders are created as needed.

        :param str path: Root-relative path of the folder to create
        """
        return self.client._perform_empty(
            "POST",
            "/projects/%s/agents/skills/%s/resources/folders/%s"
            % (self.project_key, self.id, utils.quote(path)),
        )

    def delete_resource(self, path):
        """
        Delete a resource from the skill.

        :param str path: Root-relative path of the resource to delete
        """
        return self.client._perform_empty(
            "DELETE",
            "/projects/%s/agents/skills/%s/resources/contents/%s"
            % (self.project_key, self.id, utils.quote(path)),
        )

class DSSAgentSkillSettings(DSSTaggableObjectSettings):
    def __init__(self, agent_skill, settings):
        super(DSSAgentSkillSettings, self).__init__(settings)
        self.agent_skill = agent_skill

    def get_raw(self):
        """
        Get the raw settings of the skill.

        :rtype: dict
        """
        return self._tod

    def save(self):
        """
        Saves the DSS metadata settings of the agent skill.

        This does not modify ``SKILL.md``. Use :meth:`DSSAgentSkill.put_file`
        to replace the skill file.
        """
        self.agent_skill.client._perform_empty(
            "PUT",
            "/projects/%s/agents/skills/%s" % (self.agent_skill.project_key, self.agent_skill.id),
            body=self._tod,
        )
