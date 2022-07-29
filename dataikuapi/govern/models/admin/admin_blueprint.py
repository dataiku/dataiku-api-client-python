class GovernAdminBlueprint(object):
    """
    A handle to interact with a blueprint as an admin on the Govern instance.
    Do not create this directly, use :meth:`dataikuapi.govern.BlueprintDesigner.get_blueprint`
    """

    def __init__(self, client, blueprint_id):
        self.client = client
        self.blueprint_id = blueprint_id

    @property
    def id(self):
        """
        Return the blueprint id.

        :rtype: str
        """
        return self.blueprint_id

    def get_definition(self):
        """
        Return the definition of the blueprint as an object.

        :returns: the blueprint definition as an object.
        :rtype: :class:`dataikuapi.govern.models.GovernAdminBlueprintDefinition`
        """
        definition = self.client._perform_json(
            "GET", "/admin/blueprint/%s" % self.blueprint_id).blueprint
        return GovernAdminBlueprintDefinition(self.client, self.blueprint_id, definition)

    def list_versions(self, as_objects=True):
        """
        Lists versions of this blueprint.

        :param boolean as_objects: (Optional) if True, returns a list of :class:`GovernAPIBlueprintDesignerBlueprintVersion`, else
         returns a list of dict. Each dict contains a field "id" indicating the identifier of this version
        :returns: a list - see as_objects for more information
        :rtype: list of :class: `dataikuapi.govern.models.GovernAdminBlueprintVersion` or list of dict
        """
        versions = self.client._perform_json(
            "GET", "/admin/blueprint/%s/versions" % self.blueprint_id)
        if as_objects:
            return [GovernAdminBlueprintVersion(self.client, self.blueprint_id, version["id"]["versionId"]) for version
                    in versions]
        else:
            return versions

    def create_version(self, new_identifier, blueprint_version_definition, origin_version_id=None):
        """
        Create a new blueprint version and returns a handle to interact with it.

        :param str new_identifier: the new identifier of the blueprint version. This str should be made of letters,
        digits or hyphen (-,_).
        :param dict blueprint_version_definition: The definition of the blueprint version.
        :param str origin_version_id: (Optional) The blueprint version id of the origin version id if there is one.
        :return: the created :class:`govern.models.AdminBlueprint`
        :returns The handle of the newly created blueprint
        :rtype: :class:`dataikuapi.govern.models.admin.blueprint.GovernAdminBlueprintVersion`
        """
        params = {"newIdentifier": new_identifier}
        if origin_version_id is not None:
            params["originVersionId"] = origin_version_id

        if "id" not in blueprint_version_definition:
            blueprint_version_definition["id"] = {"blueprintId": self.blueprint_id}

        self.client._perform_json("POST", "/admin/blueprint/%s/versions" % self.blueprint_id, params=params,
                                  body=blueprint_version_definition)

        return self.get_version("bv" + new_identifier)

    def get_version(self, version_id):
        """
        Returns a handle to interact with a blueprint version

        :param str version_id: id of the version
        :rtype: :class: `dataikuapi.govern.models.GovernAdminBlueprintVersion`
        """
        return GovernAdminBlueprintVersion(self.client, self.blueprint_id, version_id)


class GovernAdminBlueprintDefinition(object):
    """
    A handle of the definition of a blueprint
    Do not create this class directly, instead use :meth:`dataikuapi.govern.models.admin.GovernAdminBlueprint.get_definition`
    """

    def __init__(self, client, blueprint_id, definition):
        self.client = client
        self.blueprint_id = blueprint_id
        self.definition = definition

    def get_raw(self):
        """
        Get raw definition of a blueprint

        :return: the raw definition of blueprint, as a dict. Modifications made to the returned object are reflected
         when saving
        :rtype: dict
        """
        return self.definition

    @property
    def id(self):
        """
        Return the blueprint id.

        :return: the blueprint id
        :rtype: str
        """
        return self.blueprint_id

    @property
    def name(self):
        """
        Return the blueprint name.

        :return: the blueprint name
        :rtype: str
        """
        return self.definition["name"]

    @property
    def icon(self):
        """
        Return the blueprint icon.

        :return: the blueprint icon
        :rtype: str
        """
        return self.definition["icon"]

    @property
    def color(self):
        """
        Return the blueprint color.

        :return: the blueprint color
        :rtype: str
        """
        return self.definition["color"]

    @property
    def background_color(self):
        """
        Return the blueprint background color.

        :return: the blueprint background color
        :rtype: str
        """
        return self.definition["backgroundColor"]

    @color.setter
    def color(self, color):
        """
        Set the icon color of the blueprint

        :param str color: the new color to set, has to be in hexadecimal format.
        """
        self.definition["color"] = color

    @name.setter
    def name(self, name):
        """
        Set the icon color of the blueprint

        :param str name: the new name to set.
        """
        self.definition["name"] = name

    @icon.setter
    def icon(self, icon):
        """
        Set the icon of the blueprint

        :param str icon: the new name to set, to be chosen from: 'account_balance','account_balance_wallet',
        'account_box','account_circle','analytics','announcement','assignment','assignment_ind','assignment_late',
        'assignment_return','assignment_returned','assignment_turned_in','backup_table','batch_prediction','book',
        'book_online','bug_report','calendar_today','check_circle','code','comment_bank','contact_page','dashboard',
        'date_range','description','done','event','event_seat','extension','face','fact_check','favorite','fingerprint',
        'leaderboard','language','loyalty','pending_action','perm_contact_calendar','perm_identity','perm_media',
        'preview','print','privacy_tip','question_answer','receipt','room','rule','schedule','settings','source',
        'speaker_notes','star','sticky_note_2','table_view','thumb_up','thumb_down','timeline','toc','track_changes',
        'work','movie','new_releases','web','chat','qr_code','vpn_key','monetization_on','pie_chart','cloud','computer'
        """
        self.definition["icon"] = icon

    @background_color.setter
    def background_color(self, background_color):
        """
        Set the backgroundColor of the blueprint

        :param str background_color: the new background_color to set, has to be in hexadecimal format.
        """
        self.definition["backgroundColor"] = background_color

    def save(self):
        """
        Save this settings back to the blueprint.
        """
        self.definition = self.client._perform_json(
            "PUT", "/admin/blueprint/%s" % self.id, body=self.definition)

    def delete(self):
        """
        Delete the blueprint, including all its versions and its artifacts.
        """
        self.client._perform_empty(
            "DELETE", "/admin/blueprint/%s" % self.blueprint_id)

    # TODO: Import with version ?


class GovernAdminBlueprintVersion(object):
    """
    A handle to interact with a blueprint version on the Govern instance.
    Do not create this directly, use :meth:`dataikuapi.govern.BlueprintDesigner.Blueprint.get_version`
    """

    def __init__(self, client, blueprint_id, blueprint_version_id):
        self.client = client
        self.blueprint_id = blueprint_id
        self.blueprint_version_id = blueprint_version_id

    @property
    def id(self):
        """
        Return the blueprint version id.
        """
        return self.blueprint_version_id

    def get_definition(self):
        """
        Gets the definition of this blueprint version. If you want to modify the definition, you need to
        object call :meth:`~dataikuapi.govern.models.admin.GovernAdminBlueprintVersionDefinition.save` on the returned
        object

        :returns: The definition of the blueprint version as an object.
        :rtype: :class:`dataikuapi.govern.models.admin.GovernAdminBlueprintVersionDefinition`

        """
        definition = self.client._perform_json(
            "GET", "/admin/blueprint/%s/version/%s" % (self.blueprint_id, self.blueprint_version_id))
        return GovernAdminBlueprintVersionDefinition(self.client, self.blueprint_id, self.blueprint_version_id,
                                                     definition)

    def get_status(self):
        """
        Gets the current status of the blueprint version.

        :return: the status of the blueprint versions. Can be DRAFT, ACTIVE, or ARCHIVED
        :rtype: str

        """
        return self.client._perform_json("GET", "/admin/blueprint/%s/version/%s/status" %
                                         (self.blueprint_id, self.blueprint_version_id))

    def update_status(self, status):
        """
        Directly update the status of the blueprint version.

        :param str status: DRAFT, ACTIVE, or ARCHIVED
        """
        self.client._perform_json("PUT", "/admin/blueprint/%s/version/%s/status" %
                                  (self.blueprint_id, self.blueprint_version_id), body=status)

    def list_sign_off_configurations(self):
        """
        Gets the blueprint sign off configuration list of this blueprint version.

        :returns: The list of configuration as a Python list of dict
        :rtype: List of dict
        """

        # TODO: Throw a 404 and catch com.dataiku.dip.server.controllers.NotFoundException: Not restful ?
        return self.client._perform_json(
            "GET", "/admin/blueprint/%s/version/%s/signoffs" % (self.blueprint_id, self.blueprint_version_id))

    def get_sign_off_configuration(self, step_id):
        """
        Gets the sign off configuration for a specific step. If you want to modify the configuration, you need to call
        :meth:`~dataikuapi.govern.models.admin.GovernAdminSignOffConfiguration.save` on the returned object

        :returns: The signoff configuration as a object
        :rtype: a :class:`dataikuapi.govern.models.admin.GovernAdminSignOffConfiguration`
        """
        sign_off_config = self.client._perform_json(
            "GET", "/admin/blueprint/%s/version/%s/workflow/step/%s/signoff" %
                   (self.blueprint_id, self.blueprint_version_id, step_id))

        return GovernAdminSignOffConfiguration(self.client, self.blueprint_id, self.blueprint_version_id, step_id,
                                               sign_off_config)

    def delete_sign_off_configuration(self, step_id):
        """
        Delete the sign off configuration of a specific step.
        :param str step_id: Identifier of the step of which the sign off configuration will be deleted.
        """
        self.client._perform_empty(
            "DELETE", "/admin/blueprint/%s/version/%s/workflow/step/%s/signoff" % (self.blueprint_id,
                                                                                   self.blueprint_version_id, step_id))


class GovernAdminBlueprintVersionDefinition(object):
    """
    A handle to interact with a blueprint version definition on the Govern instance.
    Do not create this directly, use :meth:`dataikuapi.govern.models.admin.GovernAdminBlueprintVersion.get_definition`
    """

    def __init__(self, client, blueprint_id, blueprint_version_id, definition):
        self.client = client
        self.blueprint_id = blueprint_id
        self.blueprint_version_id = blueprint_version_id
        self.definition = definition

    def get_raw(self):
        """
        Get raw definition of the blueprint version.

        :return: the raw definition of blueprint, as a dict. Modifications made to the returned object are reflected
        when saving
        :rtype: dict
        """
        return self.definition

    def get_name(self):
        """
        Gets the name of the version.

        :rtype: str
        """
        return self.definition["name"]

    def get_instructions(self):
        """
        Gets the instructions for this version.

        :rtype: str
        """
        return self.definition["instructions"]

    def get_hierarchical_parent_field_id(self):
        """
        Gets the parent field id.

        :rtype: str
        """
        return self.definition["hierarchicalParentFieldId"]

    def get_field_definitions(self):
        """
        Gets the field definitions of this version. This returns a dictionary with the field ids of as the keys,
        the values are the definition of the fields.

        :rtype: dict
        """
        return self.definition["fieldDefinitions"]

    def get_field_definition(self, field_definition_id):
        """
        Gets the definition of a specific field. This returns a dictionary with the definition of the field.

        :param str field_definition_id: id of the desired field
        :rtype: dict
        """
        return self.definition["fieldDefinitions"][field_definition_id]

    def get_workflow_definition(self):
        """
        Gets the workflow definition for this version. This returns a dictionary with the step definitions.

        :rtype: dict
        """
        return self.definition["workflowDefinition"]

    def get_logical_hook_list(self):
        """
        Gets the list of the hooks for this version. This returns a list with the logical hooks.

        :rtype: list
        """
        return self.definition["logicalHookList"]

    def get_ui_definition(self):
        """
        Gets the UI definition of this versions. Returs a dict with the UI definition information.

        :rtype: dict
        """
        return self.definition["uiDefinition"]

    def save(self, danger_zone_accepted=None):
        """
        Save this definition back to the blueprint version definition.

        :param boolean danger_zone_accepted: accept the warning about existing artifacts.
        """
        params = {}
        if danger_zone_accepted is not None:
            params["dangerZoneAccepted"] = danger_zone_accepted
        self.definition = self.client._perform_json("PUT", "/admin/blueprint/%s/version/%s" % (
            self.blueprint_id, self.blueprint_version_id), params=params, body=self.definition)


class GovernAdminSignOffConfiguration(object):
    """
    A handle to interact with the signoff configuration of a blueprint version
    Do not create this directly, use :meth:`dataikuapi.govern.models.admin.GovernAdminBlueprintVersion.get_sign_off_configuration`
    """

    def __init__(self, client, blueprint_id, version_id, step_id, configuration):
        self.client = client
        self.blueprint_id = blueprint_id
        self.version_id = version_id
        self.step_id = step_id
        self.configuration = configuration

    @property
    def id(self):
        """
        Gets the step id of the signoff configuration
        :rtype: str
        """
        return self.step_id

    def get_raw(self):
        """
        Get raw definition of the signoff configuration

        :return: the raw configuration of the signoff, as a dict. Modifications made to the returned object are reflected
         when saving
        :rtype: dict
        """
        return self.configuration

    def save(self):
        """
        Save this settings back to the signoff configuration.
        """
        self.configuration = self.client._perform_json(
            "PUT", "/admin/blueprint/%s/version/%s/workflow/step/%s/signoff" % (self.blueprint_id, self.version_id,
                                                                                self.id), body=self.configuration)
