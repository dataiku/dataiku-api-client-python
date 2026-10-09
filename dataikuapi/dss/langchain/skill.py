import json

from dataiku.langchain.dku_tracer import dku_span_builder_for_callbacks

from .tool import DKUStructuredTool


def create_skill_loader_tools(skill_loader):
    def load_skill(skillRef: str, callbacks=None) -> str:
        with dku_span_builder_for_callbacks(callbacks, ignore_missing=True).subspan("DKU_AGENT_SKILL_LOAD") as span:
            span.attributes["skillRef"] = skillRef
            return json.dumps(skill_loader._load_skill(skillRef), ensure_ascii=False)

    def read_skill_resource(skillRef: str, resourcePath: str, callbacks=None):
        with dku_span_builder_for_callbacks(callbacks, ignore_missing=True).subspan("DKU_AGENT_SKILL_RESOURCE_READ") as span:
            span.attributes["skillRef"] = skillRef
            span.attributes["resourcePath"] = resourcePath
            resource = skill_loader._read_skill_resource(skillRef, resourcePath)
            if resource.get("inlineImage") is not None:
                metadata = dict(resource)
                inline_image = metadata.pop("inlineImage")
                return [
                    {"type": "text", "text": json.dumps(metadata, ensure_ascii=False)},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "data:%s;base64,%s" % (resource["mimeType"], inline_image),
                        },
                    },
                ]
            return json.dumps(resource, ensure_ascii=False)

    return [
        DKUStructuredTool.dku_from_function(
            func=load_skill,
            name=skill_loader.SKILL_LOADER_TOOL_NAME,
            description=skill_loader.SKILL_LOADER_TOOL_DESCRIPTION,
        ),
        DKUStructuredTool.dku_from_function(
            func=read_skill_resource,
            name=skill_loader.SKILL_RESOURCE_READER_TOOL_NAME,
            description=skill_loader.SKILL_RESOURCE_READER_TOOL_DESCRIPTION,
        ),
    ]
