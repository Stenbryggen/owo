from src.owo.core import registry


def test_register_component_and_lookup():
    @registry.register_component("_test_dummy_component")
    class Dummy:
        pass

    assert registry.get_component_class("_test_dummy_component") is Dummy
    assert "_test_dummy_component" in registry.component_registry()


def test_register_system_and_lookup():
    @registry.register_system("_test_dummy_system")
    class DummySystem:
        pass

    assert registry.get_system_class("_test_dummy_system") is DummySystem
    assert "_test_dummy_system" in registry.system_registry()


def test_discover_and_import_populates_real_registries():
    registry.discover_and_import("src.owo.components")
    registry.discover_and_import("src.owo.systems")

    components = registry.component_registry()
    systems = registry.system_registry()

    assert {"energy", "health", "thermal", "sleep"} <= components.keys()
    assert {"time_season", "energy_drain", "sleep_recovery", "sickness"} <= systems.keys()
