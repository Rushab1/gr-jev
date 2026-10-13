"""Check that the key in TYPESAFE_API_KEY works. Every run makes one new Jev call, counted towards JEV_CALL_LIMIT."""

from dotenv import load_dotenv

from grjev.constants import JEV_CACHE_DIR
from grjev.jev import ChoiceQuestion, JevRequest, ask, check_call_limit, request_body
from grjev.store import next_run


def main() -> None:
    """Ask Jev the routing example from TypeSafe's API reference and print the response."""
    load_dotenv()
    question = ChoiceQuestion(
        instructions="Which team should handle this?",
        criteria={
            "billing": "Payments, invoicing, refunds",
            "technical": "Bugs, outages, integrations",
            "sales": "Pricing, upgrades, new accounts",
        },
    )
    state = "Help! My payouts have been failing for 3 days."
    request = JevRequest(state=state, questions={"department": question})
    check_call_limit(1)
    # A run number that is not saved yet, so the answer comes from the API and not from a saved file.
    response = ask(request, next_run(JEV_CACHE_DIR / request.model, request_body(request)))
    if response is None:
        raise RuntimeError("Jev rejected the request")
    print(response.model_dump_json(indent=1))


if __name__ == "__main__":
    main()
