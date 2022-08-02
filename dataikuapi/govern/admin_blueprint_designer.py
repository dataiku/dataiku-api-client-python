from dataikuapi.govern.models.admin.admin_blueprint import GovernAdminBlueprint


class GovernAdminBlueprintDesigner(object):
    """
    Handle to interact with the blueprint designer
    Do not create this directly, use :meth:`dataikuapi.govern_client.get_admin_blueprint_designer()`
    """

    def __init__(self, client):
        self.client = client

    def list_blueprints(self, as_objects=True):
        """
        Lists blueprints on the Govern instance

        :param boolean as_objects: (Optional) if True, returns a list of :class:`dataikuapi.govern.models.admin.admin_blueprint.GovernAdminBlueprint`,
         else returns a list of dict. Each dict contains at least a field "id" indicating the identifier of the blueprint

        :returns: a list of blueprints
        :rtype: list of :class: `dataikuapi.govern.models.admin.admin_blueprint.GovernAdminBlueprint` or list of dict
        """
        blueprints = self.client._perform_json("GET", "/admin/blueprints")

        if as_objects:
            return [GovernAdminBlueprint(self.client, blueprint.get("blueprint").get("id")) for blueprint in blueprints]
        else:
            return blueprints

    def get_blueprint(self, blueprint_id):
        """
        Get a specific blueprint.

        :param str blueprint_id: the id of the blueprint
        :returns: an admin blueprint object
        :rtype: :class: `dataikuapi.govern.models.admin.admin_blueprint.GovernAdminBlueprint`
        """

        return GovernAdminBlueprint(self.client, blueprint_id)

    def create_blueprint(self, new_identifier, name, icon, color, background_color=""):
        """
        Create a new blueprint and returns a handle to interact with it.

        :param str new_identifier: the new identifier for the blueprint
        :param str name: the name of the blueprint
        :param str icon: the icon of the blueprint, can be chosen from: 'account_balance','account_balance_wallet',
        'account_box','account_circle','analytics','announcement','assignment','assignment_ind','assignment_late',
        'assignment_return','assignment_returned','assignment_turned_in','backup_table','batch_prediction','book',
        'book_online','bug_report','calendar_today','check_circle','code','comment_bank','contact_page','dashboard',
        'date_range','description','done','event','event_seat','extension','face','fact_check','favorite','fingerprint',
        'leaderboard','language','loyalty','pending_action','perm_contact_calendar','perm_identity','perm_media',
        'preview','print','privacy_tip','question_answer','receipt','room','rule','schedule','settings','source',
        'speaker_notes','star','sticky_note_2','table_view','thumb_up','thumb_down','timeline','toc','track_changes',
        'work','movie','new_releases','web','chat','qr_code','vpn_key','monetization_on','pie_chart','cloud','computer'
        :param str color: the color of the blueprint icon, to be specified in hexadecimal format
        :param str background_color: (Optional) the background color, to be specified in hexadecimal format
        :returns The handle of the newly created blueprint
        :rtype: :class:`dataikuapi.govern.models.admin.GovernAdminBlueprint`
        """
        result = self.client._perform_json(
            "POST", "/admin/blueprints", params={"newIdentifier": new_identifier},
            body={"name": name,
                  "icon": icon,
                  "color": color,
                  "backgroundColor": background_color})
        return GovernAdminBlueprint(self.client, result["blueprint"]["id"])
