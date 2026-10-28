#!/usr/bin/env python3
"""Walk through a complete election against a running deployment (docker compose up).

Registers an election official, creates parties and a short parliamentary
election, uploads ballots, waits for the election to close and prints the
D'Hondt seat allocation. Uses only the standard library.

    python scripts/demo.py [--auth URL] [--admin URL] [--station URL]
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone


def call(method, url, token=None, body=None, files=None):
    headers = {}
    data = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    if files is not None:
        boundary = uuid.uuid4().hex
        name, content = files
        data = (
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\n'
            f"Content-Type: text/csv\r\n\r\n{content}\r\n--{boundary}--\r\n"
        ).encode()
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    request = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            text = response.read().decode()
            return response.status, json.loads(text) if text else None
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode() or "null")


def expect(result, status=200):
    code, body = result
    if code != status:
        sys.exit(f"Unexpected response {code}: {body}")
    return body


def wait_until_up(urls):
    for _ in range(90):
        try:
            if all(call("GET", f"{u}/health")[0] == 200 for u in urls):
                return
        except OSError:
            pass
        time.sleep(2)
    sys.exit("Services did not become healthy")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--auth", default="http://localhost:5002")
    parser.add_argument("--admin", default="http://localhost:5001")
    parser.add_argument("--station", default="http://localhost:5003")
    parser.add_argument("--admin-email", default="admin@admin.com")
    parser.add_argument("--admin-password", default="1")
    args = parser.parse_args()

    wait_until_up([args.auth, args.admin, args.station])
    print("✔ all services healthy")

    admin = expect(
        call("POST", f"{args.auth}/login", body={"email": args.admin_email, "password": args.admin_password})
    )["accessToken"]
    print("✔ logged in as administrator")

    official = {
        "jmbg": "0101990710008",
        "forename": "Ana",
        "surname": "Anić",
        "email": f"official-{uuid.uuid4().hex[:6]}@example.com",
        "password": "Election2024",
    }
    expect(call("POST", f"{args.auth}/register", body=official))
    official_token = expect(
        call("POST", f"{args.auth}/login", body={"email": official["email"], "password": official["password"]})
    )["accessToken"]
    print(f"✔ registered election official {official['email']}")

    parties = {"Green Future": 420, "Workers' Union": 310, "Liberal Alliance": 230, "Fringe List": 40}
    ids = [
        expect(call("POST", f"{args.admin}/createParticipant", admin, {"name": n, "individual": False}))["id"]
        for n in parties
    ]
    now = datetime.now(timezone.utc)
    end = now + timedelta(seconds=20)
    election = {"start": now.isoformat(), "end": end.isoformat(), "individual": False, "participants": ids}
    polls = expect(call("POST", f"{args.admin}/createElection", admin, election))["pollNumbers"]
    election_id = max(e["id"] for e in expect(call("GET", f"{args.admin}/getElections", admin))["elections"])
    print(f"✔ created a parliamentary election closing at {end:%H:%M:%S} UTC, poll numbers {polls}")

    rows = [f"{uuid.uuid4()},{poll}" for poll, votes in zip(polls, parties.values()) for _ in range(votes)]
    rows += [rows[0].split(",")[0] + ",1", f"{uuid.uuid4()},99"]  # a duplicate ballot and a bad poll number
    expect(call("POST", f"{args.station}/vote", official_token, files=("ballots.csv", "\n".join(rows))))
    print(f"✔ uploaded {len(rows)} ballots through the voting station")

    print("… waiting for the election to close")
    while True:
        code, results = call("GET", f"{args.admin}/getResults?id={election_id}", admin)
        if code == 200:
            break
        time.sleep(2)

    print("\nSeat allocation (250 seats, D'Hondt, 5% census):")
    for p in results["participants"]:
        print(f"  {p['pollNumber']}. {p['name']:<18} {p['result']:>4}")
    print("Rejected ballots:")
    for v in results["invalidVotes"]:
        print(f"  {v['ballotGuid'][:8]}…  poll {v['pollNumber']:<3} {v['reason']}")

    seats = sum(p["result"] for p in results["participants"])
    if seats != 250 or len(results["invalidVotes"]) != 2:
        sys.exit("Unexpected results")


if __name__ == "__main__":
    main()
