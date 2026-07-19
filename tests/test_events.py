from src.owo.core.events import EventBus


def test_subscribe_and_publish_calls_handler_with_payload():
    bus = EventBus()
    received = []
    bus.subscribe("thing_happened", lambda payload: received.append(payload))

    bus.publish("thing_happened", {"value": 42})

    assert received == [{"value": 42}]


def test_publish_with_no_subscribers_does_nothing():
    bus = EventBus()
    bus.publish("nobody_listening")  # should not raise


def test_multiple_handlers_all_called():
    bus = EventBus()
    calls = []
    bus.subscribe("evt", lambda p: calls.append("a"))
    bus.subscribe("evt", lambda p: calls.append("b"))

    bus.publish("evt", {})

    assert calls == ["a", "b"]


def test_publish_without_payload_passes_empty_dict():
    bus = EventBus()
    received = []
    bus.subscribe("evt", lambda p: received.append(p))

    bus.publish("evt")

    assert received == [{}]
