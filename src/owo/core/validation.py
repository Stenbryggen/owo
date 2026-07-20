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


def _validate_required_fields(data: dict, required: set, filename: str) -> None:
    missing = required - set(data)
    if missing:
        raise ContentValidationError(f"{filename}: missing required field(s) {sorted(missing)}")


def validate_recipe_dict(data: dict, filename: str = "<recipe>") -> None:
    _validate_required_fields(data, {"name", "inputs", "output_item"}, filename)
    if not isinstance(data["inputs"], dict) or not data["inputs"]:
        raise ContentValidationError(f"{filename}: 'inputs' must be a non-empty object")
    if data.get("output_type", "item") not in ("item", "structure"):
        raise ContentValidationError(f"{filename}: 'output_type' must be 'item' or 'structure'")


def validate_resource_type_dict(data: dict, filename: str = "<resource_type>") -> None:
    from src.owo.core.resource_types import GrowthSpec, WorldgenSpec

    _validate_required_fields(data, {"name", "renderable_kind", "resource_type", "max_amount"}, filename)
    if data.get("on_depleted", "remove") not in ("remove", "regen"):
        raise ContentValidationError(f"{filename}: 'on_depleted' must be 'remove' or 'regen'")

    for key, spec_cls in (("growth", GrowthSpec), ("worldgen", WorldgenSpec)):
        sub = data.get(key, {})
        if not isinstance(sub, dict):
            raise ContentValidationError(f"{filename}: '{key}' must be an object")
        known = {f.name for f in dataclasses.fields(spec_cls)}
        unknown = set(sub) - known
        if unknown:
            raise ContentValidationError(f"{filename}: unknown '{key}' field(s) {sorted(unknown)}")
