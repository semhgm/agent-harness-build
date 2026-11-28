from v9 import TOOLS, TOOL_EFFECTS, isReadOnly, guardToolCall


def test_every_tool_has_effects():
    for name in TOOLS:
        assert name in TOOL_EFFECTS, f"{name} için TOOL_EFFECTS yok"


def test_unknown_tool_is_not_read_only():
    assert isReadOnly("sendEmail") is False


def test_taint_blocks_unknown_tool():
    allowed, reason, rule = guardToolCall("sendEmail", {}, True, lambda n, a: True)
    assert allowed is False
    assert rule == "taint"


if __name__ == "__main__":
    test_every_tool_has_effects()
    test_unknown_tool_is_not_read_only()
    test_taint_blocks_unknown_tool()
    print("ok")