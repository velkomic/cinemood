import argparse
import json
import sys

import psycopg

from cinemood.catalog import load_fixtures, migrate
from cinemood.config import Settings
from cinemood.embeddings import ProviderUnavailable
from cinemood.ingestion import IngestionError, ingest


def main() -> int:
    parser = argparse.ArgumentParser(description="CineMood local catalog commands")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("migrate")
    loader = commands.add_parser("load-fixtures")
    loader.add_argument("--limit", type=int, choices=range(1, 5), default=4)
    importer = commands.add_parser("ingest-tmdb")
    importer.add_argument("--target", type=int, default=1000)
    importer.add_argument(
        "--reindex",
        action="store_true",
        help="Reindex up to target stored movies; no TMDB calls",
    )
    importer.add_argument("--max-requests", type=int, default=150)
    importer.add_argument("--max-pages", type=int, default=5)
    args = parser.parse_args()
    if args.command == "ingest-tmdb" and not (
        1 <= args.target <= 1000
        and 1 <= args.max_requests <= 2000
        and 1 <= args.max_pages <= 500
    ):
        parser.error("target must be 1..1000, requests 1..2000, pages 1..500")
    settings = Settings.from_env()
    try:
        if args.command == "migrate":
            migrate(settings)
            print(json.dumps({"status": "migrated"}))
        elif args.command == "ingest-tmdb":
            print(
                json.dumps(
                    ingest(
                        settings,
                        args.target,
                        args.max_requests,
                        args.max_pages,
                        reindex=args.reindex,
                    )
                )
            )
        else:
            count = load_fixtures(settings, args.limit)
            print(json.dumps({"status": "loaded", "embedded": count}))
    except (ProviderUnavailable, IngestionError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (psycopg.Error, ValueError, OSError):
        print(
            "Catalog command failed. Check database, migrations, and snapshot storage.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
