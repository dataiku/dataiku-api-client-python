import logging
import re

from ..dataset import DSSDataset
from ..recipe import CodeRecipeSettings


class _IndentContext(object):
    def __init__(self, flow_code_generator):
        self.flow_code_generator = flow_code_generator

    def __enter__(self):
        self.flow_code_generator.cur_indent += 1

    def __exit__(self, b, c, d):
        self.flow_code_generator.cur_indent -= 1


def slugify(name):
    return re.sub(r"[^A-Za-z0-9_]", "_", name)


class FlowCodeGenerator(object):
    def __init__(self):
        self.code = ""
        self.cur_indent = 0
        self.remove_metrics_on_datasets = False
        self.remove_display_width_on_prepare = False

    def set_options(self, remove_metrics_on_datasets=False, remove_display_width_on_prepare=False):
        self.remove_metrics_on_datasets = remove_metrics_on_datasets
        self.remove_display_width_on_prepare = remove_display_width_on_prepare
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
                    entrypoint_name = "create_recipe_%s" % slugify(item.recipe_name)
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
                srcp = raw["params"]
                self.gen("    dataset = project.create_fslike_dataset(\"%s\", \"%s\", \"%s\", \"%s\")" % \
                            (dataset.dataset_name, raw["type"], srcp["connection"], srcp.get("path", "/")))
                self.gen("    settings = dataset.get_settings()")
                self.lf()

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
                            (self.objstr(srcp.get("connection")), self.objstr(srcp.get("schema")), 
                             self.objstr(srcp.get("table"))))

                    self.codegen_object_fields(srcp, templates["abstractSQLConfig"], 
                                              ["mode", "connection", "schema", "table"], "settings.get_raw_params()")
                    do_not_copy.append("params")
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

            if not self.remove_metrics_on_datasets:
                self.lf()
                self.gen("    # Metrics")
                self.codegen_object_fields(settings.get_raw()["metrics"], templates["dataset"]["metrics"], [], "settings.get_raw()[\"metrics\"]")
            do_not_copy.append("metrics")

            self.lf()
            self.gen("    # Other dataset params")
            self.codegen_object_fields(settings.get_raw(), templates["dataset"], do_not_copy, "settings.get_raw()")
           
            self.lf()
            self.gen("    settings.save()")
            self.lf()

    def _generate_code_for_recipe(self, recipe, entrypoint_name):
        logging.info("Codegen for recipe %s" % entrypoint_name)
        self.gen("def %s(project):" % entrypoint_name)
        settings = recipe.get_settings()
        raw = settings.get_recipe_raw_definition()

        templates = recipe.client._perform_json("GET", "/projects/%s/recipes/templates" % recipe.project_key)
        
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
        for (input_role, input_item) in settings._get_flat_inputs():
            if len(input_item["deps"]) > 0:
                self.gen("    settings.add_input(%s, %s, %s)" % (self.objstr(input_role),
                                                                self.objstr(input_item["ref"]),
                                                                self.objstr(input_item["deps"])))
            else:
                self.gen("    settings.add_input(%s, %s)" % (self.objstr(input_role),
                                                                self.objstr(input_item["ref"])))
        for (output_role, output_item) in settings._get_flat_outputs():
            self.gen("    settings.add_output(%s, %s, %s)" % (self.objstr(output_role),
                                                            self.objstr(output_item["ref"]),
                                                            self.objstr(output_item["appendMode"])))
        self.lf()

        types_with_obj_payload = ["join", "grouping", "shaker"]

        # A bit of "classical cleanup"
        # Remove the dirty "map" in Spark read params
        if settings.type in types_with_obj_payload and "engineParams" in settings.obj_payload:
            rp = settings.obj_payload["engineParams"].get("spark", {}).get("readParams", {})
            if rp.get("mode", "?") == "AUTO":
                rp["map"] = {}
        if raw is not None and "params" in raw and "engineParams" in raw["params"]:
            rp = raw["params"]["engineParams"].get("spark", {}).get("readParams", {})
            if rp.get("mode", "?") == "AUTO":
                rp["map"] = {}

        # And some per-type cleanup
        def cleanup_grouping():
            for grouping_key in settings.obj_payload.get("keys", []):
                for item in ["count", "last", "min", "max", "sum", "countDistinct", "stddev", "avg", "concat", "first"]:
                    if item in grouping_key and grouping_key[item] == False:
                        del grouping_key[item]
            for aggregation in settings.obj_payload.get("values", []):
                for item in ["count", "last", "min", "max", "sum", "countDistinct", "stddev", "avg", "concat", "first",
                            "concatDistinct", "$idx", "sum2", "firstLastNotNull"]:
                    if item in aggregation and aggregation.get(item, None) == False:
                        del aggregation[item]

        def cleanup_join():
            for vi in settings.raw_virtual_inputs:
                if not vi["preFilter"]["enabled"]:
                    del vi["preFilter"]

        def cleanup_shaker():
            if self.remove_display_width_on_prepare:
                if "columnWidthsByName" in settings.obj_payload:
                    del settings.obj_payload["columnWidthsByName"]

        cleanup_by_type = {
            "grouping":  cleanup_grouping,
            "join": cleanup_join,
            "shaker":  cleanup_shaker
        }

        if settings.type in cleanup_by_type:
            cleanup_by_type[settings.type]()

        # Output payload, either globally for code
        if isinstance(settings, CodeRecipeSettings):
            code = settings.get_code()
            self.gen("    # Recipe code")
            self.gen("    settings.set_payload(%s)" % self.payloadstr(code))

        # per-field for recipes with JSON payload
        elif settings.type in types_with_obj_payload:
            prefix_by_type = {
                "join": "Join details",
                "shaker": "Prepare script"
            }
            self.gen("    # %s" % (prefix_by_type.get(settings.type, "Recipe payload")))
            payload = settings.obj_payload
            payload_template = templates["payloadsByType"][settings.type]
            self.gen("    settings.set_payload(\"{}\")")
            self.codegen_object_fields(payload, payload_template, [], "settings.obj_payload")

        # Or as string for others
        elif len(settings.get_payload()) > 0:
            self.gen("    # Recipe payload")
            self.gen("    settings.set_payload(%s)" % self.payloadstr(settings.get_payload()))

        # Then params
        if settings.type in templates["paramsByType"] and "params" in raw:
            self.lf()
            self.gen("    # Type-specific parameters")
            self.codegen_object_fields(raw["params"], templates["paramsByType"][settings.type], [], 
                                       "settings.raw_params")
            do_not_copy.append("params")
        
        # And finally other recipe fields that are not params
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

    def payloadstr(self, payload):
        if payload.endswith("\n"):
            return "\"\"\"%s\"\"\"" % payload
        else:
            return "\"\"\"%s\n\"\"\"" % payload

    def objstr(self, obj):
        return ObjectFieldFormatter(self.cur_indent + 1).format(obj)

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
        
        if default_value_for_key is not None and value_for_key == default_value_for_key:
            #print("Skipping value equal to default: %s" % key)
            return
        else:
            #print("Not equal for %s"  % key)
            #print("Template: %s" % default_value_for_key)
            #print("Real:     %s" % value_for_key)
            self.gen("    %s[\"%s\"] = %s" % ( prefix, key, self.objstr(value_for_key)))


class ObjectFieldFormatter(object):
    def __init__(self, base_indent):
        self.formatters = {
            dict: self.__class__.format_dict,
            list: self.__class__.format_list,
        }
        self.sp = "    "
        self.base_indent = base_indent
        self.no_pretty_level = 0

    def format(self, value, depth=0):
        base_repr = repr(value)
        if len(base_repr) < 25:
            # This entire value is very small, don't bother pretty-priting it
            return base_repr
        elif type(value) in self.formatters:
            return self.formatters[type(value)](self, value, depth)
        else:
            return base_repr

    def format_dict(self, value, depth):
        indent = self.base_indent + depth
        if depth > 2 or self.no_pretty_level > 0:
            return repr(value)
        else:
            items = [
                "\n" + self.sp * (indent + 1) + repr(key) + ': ' + self.format(value[key], depth + 1)
                for key in value
            ]
            return '{%s}' % (','.join(items) + "\n" + self.sp * indent)

    def format_list(self, value, depth):
        indent = self.base_indent + depth
        if depth > 2 or self.no_pretty_level > 0 or len(value) == 0:
            return repr(value)
        else:
            # Big array, don't pretty-print inner
            if len(value) > 3:
                self.no_pretty_level += 1
            items = [
                "\n" + self.sp * (indent + 1) + self.format(item, depth + 1)
                for item in value
            ]
            if len(value) > 3:
                self.no_pretty_level -= 1
        return '[%s]' % (','.join(items) +  "\n" + self.sp * indent)