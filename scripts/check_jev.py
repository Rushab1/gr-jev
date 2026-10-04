"""Check that the key in TYPESAFE_API_KEY works. The first run makes one API call; later runs read the saved file."""

from dotenv import load_dotenv

from grjev.jev import ChoiceQuestion, JevRequest, ask


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
    response = ask(JevRequest(state=state, questions={"department": question}))
    print(response.model_dump_json(indent=1))


if __name__ == "__main__":
    main()
