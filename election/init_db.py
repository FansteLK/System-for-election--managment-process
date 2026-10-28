"""Create tables (and seed the admin account) for one database. Retries until the database is reachable.

Usage: python -m election.init_db authentication|election
"""

import sys
import time

from sqlalchemy.exc import OperationalError


def main(target):
    if target == "authentication":
        from election.authentication.app import create_app, init_database
    elif target == "election":
        from election.admin.app import create_app, init_database
    else:
        raise SystemExit(__doc__)

    app = create_app()
    for attempt in range(1, 61):
        try:
            init_database(app)
            print(f"{target} database ready")
            return
        except OperationalError as exc:
            print(f"Waiting for {target} database (attempt {attempt}): {exc.orig}")
            time.sleep(2)
    raise SystemExit(f"Could not reach the {target} database")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
