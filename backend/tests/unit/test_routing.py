import asyncio

from app.agents.routing import increment_retry_count, route_after_critic, route_after_security


def test_route_after_security_blocks_on_injection():
    assert route_after_security({"injection_detected": True}) == "blocked"


def test_route_after_security_proceeds_when_clear():
    assert route_after_security({"injection_detected": False}) == "coverage_validator"
    assert route_after_security({}) == "coverage_validator"


def test_route_after_critic_finalizes_on_high_score():
    state = {"critic_score": 0.9, "retry_count": 0}
    assert route_after_critic(state, score_threshold=0.8, max_retries=2) == "final_output"


def test_route_after_critic_retries_on_low_score_within_budget():
    state = {"critic_score": 0.5, "retry_count": 0}
    assert route_after_critic(state, score_threshold=0.8, max_retries=2) == "prepare_retry"


def test_route_after_critic_finalizes_when_retries_exhausted_regardless_of_score():
    """This is the guarded exit that prevents the spec's named failure mode
    (infinite retry loop) — even a persistently low score must terminate."""
    state = {"critic_score": 0.2, "retry_count": 2}
    assert route_after_critic(state, score_threshold=0.8, max_retries=2) == "final_output"


def test_increment_retry_count():
    result = asyncio.run(increment_retry_count({"retry_count": 1}))
    assert result == {"retry_count": 2}


def test_increment_retry_count_defaults_to_zero():
    result = asyncio.run(increment_retry_count({}))
    assert result == {"retry_count": 1}
