import importlib
import pkgutil
from typing import Callable, Dict, Type

_COMPONENT_REGISTRY: Dict[str, Type] = {}
_SYSTEM_REGISTRY: Dict[str, Type] = {}


def register_component(name: str) -> Callable[[Type], Type]:
    def decorator(cls: Type) -> Type:
        _COMPONENT_REGISTRY[name] = cls
        return cls
    return decorator


def register_system(name: str) -> Callable[[Type], Type]:
    def decorator(cls: Type) -> Type:
        _SYSTEM_REGISTRY[name] = cls
        return cls
    return decorator


def get_component_class(name: str) -> Type:
    return _COMPONENT_REGISTRY[name]


def get_system_class(name: str) -> Type:
    return _SYSTEM_REGISTRY[name]


def component_registry() -> Dict[str, Type]:
    return dict(_COMPONENT_REGISTRY)


def system_registry() -> Dict[str, Type]:
    return dict(_SYSTEM_REGISTRY)


def discover_and_import(package_name: str) -> None:
    """Import every module under package_name so its @register_* decorators run."""
    package = importlib.import_module(package_name)
    for _, module_name, _ in pkgutil.iter_modules(package.__path__, prefix=f"{package_name}."):
        importlib.import_module(module_name)
