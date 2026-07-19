import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from src.owo.components import (  # noqa: F401 - registers components
    energy,
    health,
    position,
    quest,
    renderable,
    skills,
    sleep,
    thermal,
    wallet,
)
from src.owo.core import registry
from src.owo.core.validation import ContentValidationError, validate_entity_dict

CONTENT_DIR = Path(__file__).resolve().parent.parent / "content" / "entities"


def test_all_content_entity_files_validate():
    files = list(CONTENT_DIR.glob("*.json"))
    assert files, "expected at least one content/entities/*.json file"

    for path in files:
        data = json.loads(path.read_text())
        validate_entity_dict(data)


def test_unknown_component_type_is_rejected():
    data = {"name": "X", "components": [{"type": "does_not_exist", "params": {}}]}
    with pytest.raises(ContentValidationError):
        validate_entity_dict(data)


def test_unknown_param_is_rejected():
    data = {"name": "X", "components": [{"type": "energy", "params": {"bogus": 1}}]}
    with pytest.raises(ContentValidationError):
        validate_entity_dict(data)


def test_missing_required_param_is_rejected():
    @registry.register_component("_test_requires_field")
    @dataclass
    class RequiresField:
        must_have: int

    data = {"name": "X", "components": [{"type": "_test_requires_field", "params": {}}]}
    with pytest.raises(ContentValidationError):
        validate_entity_dict(data)
