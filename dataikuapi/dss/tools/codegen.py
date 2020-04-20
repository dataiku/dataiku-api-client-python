import json, copy, re
from dataikuapi.dss.recipe import *
from dataikuapi.dss.dataset import *

class _IndentContext(object):
    def __init__(self, flow_code_generator):
        self.flow_code_generator = flow_code_generator

    def __enter__(self):
        self.flow_code_generator.cur_indent += 1

    def __exit__(self, b, c, d):
        self.flow_code_generator.cur_indent -= 1

def output_to_code(obj):
        if isinstance(obj, basestring):
            return "\"%s\"" % obj
        else:
            return obj

def slugify(name):
    return re.sub("[^A-Za-z0-9_]", "_", name)

class FlowCodeGenerator(object):
    def __init__(self):
        self.code = ""
        self.cur_indent = 0

    def set_options(self):
        pass


    def generate_code_for_dataset(self, dataset):
        entrypoint_name = "create_dataset_%s" % dataset.dataset_name
        self._generate_code_for_dataset(dataset, entrypoint_name)
        return self.code

    def generate_code_for_recipe(self, recipe):
        entrypoint_name = "create_recipe_%s" % recipe.recipe_name
        self._generate_code_for_recipe(recipe, entrypoint_name)
        return self.code

    def generate_code_for_project(self, project, entrypoint_name = None):
        self.gen("import json")
        self.gen("")

        if entrypoint_name is None:
            entrypoint_name = "create_flow_for_project"

        self.gen("def %s(project):" % entrypoint_name)
        
        flow_graph = project.get_flow().get_graph()
        flow_items = flow_graph.get_items_in_traversal_order(as_type="object")

        entrypoints_to_call = []
        with _IndentContext(self) as ic:
            for item in flow_items:
                if isinstance(item, DSSDataset):
                    entrypoint_name = "create_dataset_%s" % slugify(item.dataset_name)
                    self._generate_code_for_dataset(item, entrypoint_name)
                else:
                    entrypoint_name = "create_recipe%s" % slugify(item.recipe_name)
                    self._generate_code_for_recipe(item, entrypoint_name)
                entrypoints_to_call.append(entrypoint_name)

            self.gen("")
            self.gen("# Actual creation of the Flow from the individual functions")
            for ep in entrypoints_to_call:
                self.gen("%s(project)" % ep)

        return self.code

    def _generate_code_for_dataset(self, dataset, entrypoint_name):
            self.gen("def %s(project):" % entrypoint_name)
            settings = dataset.get_settings()
            raw = settings.get_raw()
            
            templates = dataset.client._perform_json("GET", "/projects/X/datasets/templates")
            
            do_not_copy = [
                "projectKey",
                "name",
                "type",
                "versionTag",
                "creationTag",
                "schema"
            ]

            self.gen("    # Base dataset params")
            
            if raw["type"] == "UploadedFiles":
                self.gen("    dataset = project.create_upload_dataset(\"%s\")" % dataset.dataset_name)
                self.gen("    settings = dataset.get_settings()")
                self.lf()
                
                self.codegen_object_fields_explicit(settings.get_raw(), templates["dataset"], ["params"], "settings.get_raw()")
                do_not_copy.append("params")

            elif raw["type"] in DSSDataset.FS_TYPES:
                self.gen("    dataset = project.create_dataset(\"%s\", \"%s\")" % (dataset.dataset_name, raw["type"]))
                self.gen("    settings = dataset.get_settings()")
                self.lf()

                srcp = raw["params"]
                self.gen("    settings.set_connection_and_path(%s, %s)" % \
                             (output_to_code(srcp.get("connection")), output_to_code(srcp.get("path"))))
                self.codegen_object_fields(srcp, templates["abstractFSConfig"], 
                                              ["connection", "path"], "settings.get_raw_params()")
                do_not_copy.append("params")
            elif raw["type"] in DSSDataset.SQL_TYPES:
                self.gen("    dataset = project.create_dataset(\"%s\", \"%s\")" % (dataset.dataset_name, raw["type"]))
                self.gen("    settings = dataset.get_settings()")
                self.lf()

                srcp = raw["params"]
                if srcp.get("mode", None) == "table":
                    self.gen("    settings.set_table(%s, %s, %s)" % \
                            (output_to_code(srcp.get("connection")), output_to_code(srcp.get("schema")), 
                             output_to_code(srcp.get("table"))))

                    self.codegen_object_fields(srcp, templates["abstractSQLConfig"], 
                                              ["mode", "connection", "schema", "table"], "settings.get_raw_params()")
            else:
                self.gen("    dataset = project.create_dataset(\"%s\", \"%s\")" % (dataset.dataset_name, raw["type"]))
                self.gen("    settings = dataset.get_settings()")

                self.codegen_object_fields_explicit(settings.get_raw(), templates["dataset"], ["params"], "settings.get_raw()")
                do_not_copy.append("params")

            # Copy of format params
            if "formatType" in raw:
                self.lf()
                self.gen("    # Format params")

                handled = False

                if raw["formatType"] == "csv":
                    csv_format = raw["formatParams"]
                    self.gen("    settings.set_csv_format(separator=\"%s\", style=\"%s\", skip_rows_before=%d, header_row=%s, skip_rows_after=%d)"%\
                                (csv_format.get("separator", None), csv_format["style"], csv_format["skipRowsBeforeHeader"],\
                                    csv_format["parseHeaderRow"], csv_format["skipRowsAfterHeader"]))

                    self.codegen_object_fields(csv_format, templates["csvFormat"], 
                                              ["separator", "style", "skipRowsBeforeHeader",
                                                "parseHeaderRow", "skipRowsAfterHeader", "probableNumberOfRecords"],
                                               "settings.get_raw_format_params()")
                else:
                    self.codegen_object_fields_explicit(settings.get_raw(), templates["dataset"], ["formatType", "formatParams"],
                                                        "settings.get_raw()")
                do_not_copy.extend(["formatType", "formatParams"])

            self.lf()
            self.gen("    # Schema")
            for column in settings.get_raw()["schema"]["columns"]:
                self.gen("    settings.add_raw_schema_column(%s)" % column)

            self.lf()
            self.gen("    # Other dataset params")
            self.codegen_object_fields(settings.get_raw(), templates["dataset"], do_not_copy, "settings.get_raw()")
           
            self.lf()
            self.gen("    settings.save()")
            self.lf()

    def _generate_code_for_recipe(self, recipe, entrypoint_name):
        self.gen("def %s(project):" % entrypoint_name)
        settings = recipe.get_settings()
        raw = settings.get_recipe_raw_definition()
        
        template = {"tags":[], "optionalDependencies": False, "redispatchPartitioning": False,
                    "maxRunningActivities": 0, "neverRecomputeExistingPartitions" : False,
                    "customFields":{}, "customMeta": {"kv":{}}, "checklists" : {"checklists":[]}}
        
        do_not_copy = [
            "projectKey",
            "name",
            "type",
            "versionTag",
            "creationTag",
            "inputs",
            "outputs"
        ]
        
        self.gen("    # Create the recipe as a blank recipe")
        self.gen("    builder = project.new_recipe(\"%s\", \"%s\")" % (raw["type"], recipe.recipe_name))
        self.gen("    builder.set_raw_mode()")
        self.gen("    recipe = builder.create()")
        self.lf()
        self.gen("    # Setup the recipe")
        self.gen("    settings = recipe.get_settings()"    )

        self.lf()
        self.gen("    # Recipe inputs/outputs")
        self.codegen_object_fields_explicit(raw, template, ["inputs", "outputs"], "settings.get_recipe_raw_definition()")
        self.lf()
        
        self.gen("    # Recipe payload")
        if isinstance(settings, CodeRecipeSettings):
            code = settings.get_code()
            self.gen("    settings.set_code(\"\"\"%s\n\"\"\")" % code)
        else:
            self.gen("    # No specific handling, simply copy payload")
            self.gen("    settings.set_payload(\"\"\"%s\n\"\"\")" % settings.get_payload())

        self.lf()
        self.gen("    # Other parameters")
        self.codegen_object_fields(raw, template, do_not_copy, "settings.get_recipe_raw_definition()")
        self.lf()
        self.gen("    settings.save()")
        self.lf()

    # Helpers

    def gen(self, code):
        self.code += "%s%s\n" % (" " * (4 * self.cur_indent), code)

    def lf(self):
        self.code += "\n"

    def codegen_object_fields_explicit(self, object, template, copy, prefix):
        for key in copy:
            if not key in object:
                continue
            self.codegen_object_field(object, key, template, prefix)

    def codegen_object_fields(self, object, template, do_not_copy, prefix):
        for key in object.keys():
            if key in do_not_copy:
                continue
            self.codegen_object_field(object, key, template, prefix)

    def codegen_object_field(self, object, key, template, prefix):
        value_for_key = object[key]
        default_value_for_key = template.get(key, None)
        
        if default_value_for_key is not None and json.dumps(value_for_key) == json.dumps(default_value_for_key):
            #print("Skipping value equal to default: %s" % key)
            return
        else:
            #print("Not equal for %s"  % key)
            #print("Template: %s" % default_value_for_key)
            #print("Real:     %s" % value_for_key)
            self.gen("    %s[\"%s\"] = %s" % ( prefix, key, output_to_code(value_for_key)))
