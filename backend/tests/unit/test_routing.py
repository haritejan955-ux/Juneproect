from app.agents.routing import prepare_retry, route_after_critic, route_after_parser


def test_route_after_parser_blocked():
    assert route_after_parser({"injection_detected": True}) == "blocked"


def test_route_after_parser_continue():
    assert route_after_parser({"injection_detected": False}) == "continue"


def test_route_after_critic_approved_goes_to_final_output():
    assert route_after_critic({"critique_approved": True, "retry_count": 0}) == "final_output"


def test_route_after_critic_retries_when_under_limit():
    assert route_after_critic({"critique_approved": False, "retry_count": 0}) == "retry"


def test_route_after_critic_stops_after_max_retries():
    assert route_after_critic({"critique_approved": False, "retry_count": 2}) == "final_output"


def test_prepare_retry_increments_count():
    result = prepare_retry({"retry_count": 1})
    assert result["retry_count"] == 2
    assert result["audit_log"][0]["agent"] == "prepare_retry"
