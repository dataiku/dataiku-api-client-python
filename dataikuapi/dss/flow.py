from .utils import AnyLoc
from .recipe import DSSRecipeDefinitionAndPayload
import logging
class DSSProjectFlow(object):
    def __init__(self, client, project):
        self.client = client
        self.project = project


    def replace_input_computable(self, current_ref, new_ref, type="DATASET"):
        """
        This method replaces all references to a "computable" (Dataset, Managed Folder or Saved Model)
        as input of recipes in the whole Flow by a reference to another computable.

        No specific checks are performed. It is your responsibility to ensure that the schema
        of the new dataset will be compatible with the previous one (in the case of datasets).

        If `new_ref` references an object in a foreign project, this method will automatically
        ensure that `new_ref` is exposed to the current project

        :param current_ref str: Either a "simple" object name (dataset name, model id, managed folder id)
                    or a foreign object reference in the form "FOREIGN_PROJECT_KEY.local_id")
        :param new_ref str: Either a "simple" object name (dataset name, model id, managed folder id)
                    or a foreign object reference in the form "FOREIGN_PROJECT_KEY.local_id")
        :param type str: The type of object being replaced (DATASET, SAVED_MODEL or MANAGED_FOLDER)
        """

        new_loc = AnyLoc.from_ref(self.project.project_key, new_ref)

        if new_loc.project_key != self.project.project_key:
            logging.debug("New ref is in project %s, exposing it to project %s" % (new_loc.project_key, self.project.project_key))
            new_ref_src_project = self.client.get_project(new_loc.project_key)
            settings = new_ref_src_project.get_settings()
            settings.add_exposed_object(type, new_loc.object_id, self.project.project_key)
            settings.save()

        for recipe in self.project.list_recipes():
            fake_rap = DSSRecipeDefinitionAndPayload({"recipe" : recipe})
            if fake_rap.has_input(current_ref):
                logging.debug("Recipe %s has %s as input, performing the replacement by %s"% \
                    (recipe["name"], current_ref, new_ref))
                recipe_obj = self.project.get_recipe(recipe["name"])
                dap = recipe_obj.get_definition_and_payload()
                dap.replace_input(current_ref, new_ref)
                recipe_obj.set_definition_and_payload(dap)
