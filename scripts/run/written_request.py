"""Send one request written for the paper and print the probabilities of each of its lists or yes/no questions.

The requests are in scripts/run/requests/. The response is saved like every response, so a second run of the
command calls nothing. --run 2 sends the same request again and saves the answer under run number 2. A call to Jev
counts towards JEV_CALL_LIMIT.
"""

import argparse

from dotenv import load_dotenv

from grjev.constants import GATEWAY_MODELS, JEV_MODEL, WRITTEN_REQUESTS_DIR
from grjev.jev import ChoiceAnswer, NoulAnswer, ask, check_call_limit, response_path
from grjev.written import read_written


def parse_args() -> argparse.Namespace:
    """Read the name of the request and the model."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", choices=sorted(path.stem for path in WRITTEN_REQUESTS_DIR.glob("*.json")))
    parser.add_argument("--model", default=JEV_MODEL, choices=[JEV_MODEL, *GATEWAY_MODELS])
    parser.add_argument("--run", type=int, default=1, help="the number of the repeat of the request")
    return parser.parse_args()


def main() -> None:
    """Ask the model the request and print the answer for each list, with the probabilities from the highest."""
    args = parse_args()
    load_dotenv()
    request = read_written(WRITTEN_REQUESTS_DIR / f"{args.request}.json", args.model)
    check_call_limit(not response_path(request, args.run).exists(), args.model)
    response = ask(request, args.run)
    if response is None:
        raise RuntimeError(f"{args.model} rejected the request")
    print(f"state: {request.state}")
    for name, answer in response.answers.items():
        if isinstance(answer, ChoiceAnswer):
            ranked = sorted(answer.probabilities.items(), key=lambda entry: entry[1], reverse=True)
            print(f"{args.model} {name}: " + ", ".join(f"{option} {value}" for option, value in ranked))
        elif isinstance(answer, NoulAnswer):
            print(f"{args.model} {name}: yes {answer.noul}")
        else:
            print(f"{args.model} {name}: {answer.type}")
    print(f"input tokens: {response.usage.input_tokens}")


if __name__ == "__main__":
    main()
