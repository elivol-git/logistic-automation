#!/usr/bin/env python
"""CLI helper for managing the SSM whitelist."""
import sys
import json
import os
from pathlib import Path

# Load .env from project root
env_path = Path(__file__).parents[4] / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

import boto3

REGION = os.environ.get("AWS_REGION", "eu-north-1")
PARAM  = os.environ.get("SSM_WHITELIST_PARAM", "/gmail-automation/whitelist")

def get_client():
    return boto3.client(
        "ssm",
        region_name=REGION,
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    )

def load() -> list[str]:
    r = get_client().get_parameter(Name=PARAM)
    return json.loads(r["Parameter"]["Value"])

def save(emails: list[str]):
    get_client().put_parameter(
        Name=PARAM,
        Value=json.dumps(emails),
        Type="String",
        Overwrite=True,
    )

def cmd_list():
    emails = load()
    if not emails:
        print("Whitelist is empty.")
    else:
        print(f"Whitelist ({len(emails)} email(s)):")
        for i, e in enumerate(emails, 1):
            print(f"  {i}. {e}")

def cmd_add(email: str):
    email = email.strip().lower()
    emails = load()
    if email in emails:
        print(f"Already in whitelist: {email}")
        return
    emails.append(email)
    save(emails)
    print(f"Added: {email}")
    print(f"Whitelist now has {len(emails)} email(s).")

def cmd_remove(email: str):
    email = email.strip().lower()
    emails = load()
    if email not in emails:
        print(f"Not found in whitelist: {email}")
        return
    emails.remove(email)
    save(emails)
    print(f"Removed: {email}")
    print(f"Whitelist now has {len(emails)} email(s).")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: whitelist.py [list|add <email>|remove <email>]")
        sys.exit(1)
    command = sys.argv[1]
    if command == "list":
        cmd_list()
    elif command == "add" and len(sys.argv) == 3:
        cmd_add(sys.argv[2])
    elif command == "remove" and len(sys.argv) == 3:
        cmd_remove(sys.argv[2])
    else:
        print("Usage: whitelist.py [list|add <email>|remove <email>]")
        sys.exit(1)
