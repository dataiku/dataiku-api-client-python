import base64
import json

from requests import utils

from ..utils import dku_basestring_type

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

    def get_resource_manifest(self):
        """
        Get the flat agent-readable resource manifest for this skill.

        :rtype: list[dict]
        """
        return self.client._perform_json(
            "GET",
            "/projects/%s/agents/skills/%s/resources/manifest" % (self.project_key, self.id),
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


class DSSAgentSkillLoader(object):
    """
    Makes an explicit set of agent skills available to an LLM through
    instruction-loading and resource-reading tools.

    .. important::
        Do not instantiate this class directly. Use
        :meth:`dataikuapi.dss.project.DSSProject.get_agent_skill_loader`.
    """

    SKILL_LOADER_TOOL_NAME = "dku_skill_load"
    SKILL_RESOURCE_READER_TOOL_NAME = "dku_skill_read_resource"
    SKILL_LOADER_TOOL_DESCRIPTION = (
        "Loads the full instructions and bundled resource manifest for one available Skill by its skillRef. "
        "Use this only when an exposed Skill is clearly relevant to the current task."
    )
    SKILL_RESOURCE_READER_TOOL_DESCRIPTION = (
        "Reads one text or image resource from a loaded Skill by skillRef and exact resourcePath. "
        "Use this only when a previously loaded Skill lists a resource that is materially relevant to the current task."
    )

    def __init__(self, project, skill_refs=None):
        if isinstance(skill_refs, dku_basestring_type):
            skill_refs = [skill_refs]
        self.project = project
        self._skills = {}
        for skill_ref in skill_refs or []:
            self.add_skill(skill_ref)

    def add_skill(self, skill_ref):
        """
        Add one skill to the set exposed by this loader.

        Adding the same reference more than once has no effect.

        :param str skill_ref: Local skill ID or shared skill smart reference
        """
        if not isinstance(skill_ref, dku_basestring_type):
            raise TypeError("skill_ref must be a string")
        skill_ref = skill_ref.strip()
        if not skill_ref:
            raise ValueError("skill_ref must not be empty")
        if skill_ref in self._skills:
            return

        skill = self.project.get_agent_skill(skill_ref)
        content = skill.get_skill_content()
        resources = []
        for resource in skill.get_resource_manifest():
            readable_as = None
            if resource.get("textEditable"):
                readable_as = "text"
            elif resource.get("imageReadable"):
                readable_as = "image"
            resources.append({
                "path": resource.get("path"),
                "mimeType": resource.get("mimeType"),
                "readableAs": readable_as,
            })

        self._skills[skill_ref] = {
            "handle": skill,
            "name": content.get("name") or skill_ref,
            "description": content.get("description") or "",
            "metadata": content.get("metadata") or {},
            "instructions": content.get("instructions") or "",
            "resources": resources,
            "resourcesByPath": dict((resource["path"], resource) for resource in resources),
        }

    def get_prompt(self):
        """
        Build the lightweight prompt that exposes available skills.

        Full skill instructions and resource contents are deliberately omitted.

        :rtype: str
        """
        if not self._skills:
            return ""

        lines = [
            "Exposed Skills:",
            "You initially know only the lightweight metadata for these Skills.",
            "If a Skill is clearly relevant, call %s with its skillRef to load its full instructions and resource manifest before proceeding."
            % self.SKILL_LOADER_TOOL_NAME,
            "After loading a Skill, if a listed resource whose readableAs field is text or image would materially help answer the user, call %s with that same skillRef and the exact resourcePath to read it."
            % self.SKILL_RESOURCE_READER_TOOL_NAME,
            "Loading a Skill does not grant any extra tools or permissions. Skills only provide instructions and bundled resource files.",
        ]
        for skill_ref, skill in self._skills.items():
            lines.append(
                "- skillRef: %s | name: %s | description: %s"
                % (skill_ref, skill["name"], skill["description"])
            )
            if skill["metadata"]:
                lines.append(
                    "  metadata: %s"
                    % json.dumps(skill["metadata"], ensure_ascii=False, sort_keys=True)
                )
        return "\n".join(lines)

    def as_langchain_structured_tools(self):
        """
        Return the skill instruction loader and resource reader as
        LangChain structured tools.

        :rtype: list[langchain_core.tools.StructuredTool]
        """
        from dataikuapi.dss.langchain.skill import create_skill_loader_tools
        return create_skill_loader_tools(self)

    def _as_llm_mesh_tools(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": self.SKILL_LOADER_TOOL_NAME,
                    "description": self.SKILL_LOADER_TOOL_DESCRIPTION,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "skillRef": {
                                "type": "string",
                                "description": "The reference of an exposed Skill.",
                            },
                        },
                        "required": ["skillRef"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": self.SKILL_RESOURCE_READER_TOOL_NAME,
                    "description": self.SKILL_RESOURCE_READER_TOOL_DESCRIPTION,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "skillRef": {
                                "type": "string",
                                "description": "The reference of the loaded Skill.",
                            },
                            "resourcePath": {
                                "type": "string",
                                "description": "The exact path of a resource listed by the loaded Skill.",
                            },
                        },
                        "required": ["skillRef", "resourcePath"],
                    },
                },
            },
        ]

    def _load_skill(self, skill_ref):
        skill = self._get_skill(skill_ref)
        return {
            "skillRef": skill_ref,
            "name": skill["name"],
            "description": skill["description"],
            "metadata": skill["metadata"],
            "instructions": skill["instructions"],
            "resources": skill["resources"],
        }

    def _read_skill_resource(self, skill_ref, resource_path):
        skill = self._get_skill(skill_ref)
        resource = skill["resourcesByPath"].get(resource_path)
        if resource is None:
            raise ValueError("Unknown resource for Skill %s: %s" % (skill_ref, resource_path))
        readable_as = resource.get("readableAs")
        if readable_as is None:
            raise ValueError("Resource is not readable by the agent: %s" % resource_path)

        content = skill["handle"].get_file(resource_path).content
        result = {
            "skillRef": skill_ref,
            "path": resource_path,
            "mimeType": resource["mimeType"],
        }
        if readable_as == "text":
            result["content"] = content.decode("utf-8")
        else:
            result["inlineImage"] = base64.b64encode(content).decode("ascii")
        return result

    def _run_llm_mesh_tool(self, tool_name, input):
        if tool_name == self.SKILL_LOADER_TOOL_NAME:
            return {
                "output": self._load_skill(input["skillRef"]),
                "parts": [],
            }
        if tool_name == self.SKILL_RESOURCE_READER_TOOL_NAME:
            resource = self._read_skill_resource(input["skillRef"], input["resourcePath"])
            inline_image = resource.pop("inlineImage", None)
            parts = []
            if inline_image is not None:
                parts.append({
                    "type": "IMAGE_INLINE",
                    "inlineImage": inline_image,
                    "imageMimeType": resource["mimeType"],
                })
            return {
                "output": resource,
                "parts": parts,
            }
        raise ValueError("Unknown Skill loader tool: %s" % tool_name)

    def _get_skill(self, skill_ref):
        skill = self._skills.get(skill_ref)
        if skill is None:
            raise ValueError("Unknown exposed Skill: %s" % skill_ref)
        return skill


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
