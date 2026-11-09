import argparse
import json
import sys

import psycopg

from cinemood.catalog import load_fixtures, migrate
from cinemood.config import Settings
from cinemood.embeddings import ProviderUnavailable


def main() -> int:
    parser = argparse.ArgumentParser(description="CineMood local catalog commands")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("migrate")
    loader = commands.add_parser("load-fixtures")
    loader.add_argument("--limit", type=int, choices=range(1, 5), default=4)
    args = parser.parse_args()
    settings = Settings.from_env()
    try:
        if args.command == "migrate":
            migrate(settings)
            print(json.dumps({"status": "migrated"}))
        else:
            count = load_fixtures(settings, args.limit)
            print(json.dumps({"status": "loaded", "embedded": count}))
    except ProviderUnavailable as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (psycopg.Error, ValueError):
        print(
            "Catalog command failed. Check database availability and migrations.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
