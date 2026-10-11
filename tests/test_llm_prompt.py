"""Planner/observer prompts are generated from the live TOOLS registry (P1.1)."""
from vendorlens import llm
from vendorlens.tools import TOOLS


def test_every_tool_is_listed_in_the_planner_prompt():
    for name in TOOLS:
        assert name in llm.PLAN_SYSTEM, f"{name} missing from PLAN_SYSTEM"


def test_raw_socket_tools_are_marked_as_last_resort():
    for name in llm._RAW_SOCKET:
        assert name in llm.PLAN_SYSTEM
    assert "raw-socket" in llm.PLAN_SYSTEM


def test_planner_and_share_descriptions_from_registry():
    for name, mod in TOOLS.items():
        head = getattr(mod, "DESCRIPTION", "").split(". ")[0]
        assert head in llm.PLAN_SYSTEM


def test_observer_prompt_lists_tools():
    for name in TOOLS:
        assert name in llm.OBSERVER_SYSTEM
