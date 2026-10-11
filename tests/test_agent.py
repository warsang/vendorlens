"""Agent behaviour: sanitizing, rule-based replanning, retry recovery (P1.2, P1.3)."""
import asyncio

from vendorlens import agent, tracing


def test_sanitize_drops_unknown_tools_and_fills_args():
    raw = [
        {"tool": "rdap_lookup", "why": "x"},
        {"tool": "not_a_tool"},
        "garbage",
        {"tool": "ct_logs", "args": {"domain": "keep.example"}},
    ]
    out = agent._sanitize_steps(raw, "x.example")
    tools = [s["tool"] for s in out]
    assert tools == ["rdap_lookup", "ct_logs"]
    assert out[0]["args"]["domain"] == "x.example"
    assert out[1]["args"]["domain"] == "keep.example"


def test_rule_replan_adds_phishing_check_for_young_domain():
    step = {"id": "s1", "tool": "rdap_lookup", "args": {"domain": "x.example"},
            "why": ""}
    result = {"ok": True, "data": {"found": True, "age_days": 40}}
    extras = agent._rule_replan(step, result, {"findings": {}}, "x.example",
                                set())
    assert [s["tool"] for s in extras] == ["phishtank_check"]


def test_rule_replan_no_phishing_check_for_old_domain():
    step = {"id": "s1", "tool": "rdap_lookup", "args": {"domain": "x.example"},
            "why": ""}
    result = {"ok": True, "data": {"found": True, "age_days": 3000}}
    extras = agent._rule_replan(step, result, {"findings": {}}, "x.example",
                                set())
    assert extras == []


def test_rule_replan_www_fallback_on_homepage_failure():
    step = {"id": "s6", "tool": "fetch_homepage", "args": {"domain": "x.example"},
            "why": ""}
    result = {"ok": False, "error": "ConnectError"}
    extras = agent._rule_replan(step, result, {"findings": {}}, "x.example",
                                set())
    assert len(extras) == 1 and extras[0]["tool"] == "fetch_homepage"
    assert extras[0]["args"]["domain"] == "www.x.example"


def test_demo_run_adds_phishing_check_via_rule():
    state = asyncio.run(agent.run_investigation(
        "acme-cloud-services.example", demo=True, scenario="suspicious"))
    tools_run = {sr["tool"] for sr in state["step_results"]}
    assert "phishtank_check" in tools_run  # arrived via rule-based replanning
    assert state["replans"]["rule"] >= 1


def test_injected_failure_shows_retry_then_recovery(tmp_path):
    trace = tmp_path / "trace.jsonl"
    tracing.set_trace_file(trace, "test")
    try:
        state = asyncio.run(agent.run_investigation(
            "acme-cloud-services.example", demo=True, scenario="suspicious",
            inject={"ct_logs": 1}))
    finally:
        tracing.set_trace_file(None, "")
    ct = next(sr for sr in state["step_results"] if sr["tool"] == "ct_logs")
    assert ct["ok"] is True
    assert ct["attempts"] >= 2          # first attempt injected, then retried
    kinds = [__import__("json").loads(line)["kind"]
             for line in trace.read_text().splitlines() if line.strip()]
    assert "tool_retry" in kinds and "tool_recovered" in kinds


def test_two_demo_runs_in_one_process_do_not_share_domain():
    # Regression: _sanitize_steps must not mutate the shared DEMO_PLAN args.
    first = asyncio.run(agent.run_investigation(
        "alpha.example", demo=True, scenario="suspicious"))
    second = asyncio.run(agent.run_investigation(
        "beta.example", demo=True, scenario="suspicious"))
    assert first["domain"] == "alpha.example"
    assert second["domain"] == "beta.example"
    # The second run's own tool args must carry its own domain.
    rdap = second["findings"]["rdap_lookup"]["data"]
    assert rdap.get("domain") == "beta.example"
    # DEMO_PLAN constant is untouched.
    assert agent.DEMO_PLAN[0]["args"] == {}
