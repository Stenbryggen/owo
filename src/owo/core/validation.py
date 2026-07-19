import dataclasses

from src.owo.core.registry import get_component_class


class ContentValidationError(ValueError):
    pass


def _required_field_names(cls) -> set:
    return {
        f.name
        for f in dataclasses.fields(cls)
        if f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING
    }


def validate_entity_dict(data: dict) -> None:
    if not isinstance(data.get("components"), list):
        raise ContentValidationError("entity must have a 'components' list")

    for component_data in data["components"]:
        type_name = component_data.get("type")
        try:
            cls = get_component_class(type_name)
        except KeyError:
            raise ContentValidationError(f"unknown component type: {type_name!r}")

        params = component_data.get("params", {})
        field_names = {f.name for f in dataclasses.fields(cls)}

        unknown = set(params) - field_names
        if unknown:
            raise ContentValidationError(f"unknown params {unknown} for component {type_name!r}")

        missing = _required_field_names(cls) - set(params)
        if missing:
            raise ContentValidationError(
                f"missing required params {missing} for component {type_name!r}"
            )
