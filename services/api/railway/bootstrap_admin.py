"""Pre-deploy step 3: create the first dashboard admin from variables.

Upstream's dashboard lets the first visitor register the admin account
(POST /auth/register is open until a user exists). On a public Railway
domain that is a race, so this creates the admin before the API starts,
like upstream's `make bootstrap` does, using upstream's own models and
password hashing. It only acts while the users table is empty: changing the
variables later never touches an existing account (use the dashboard's
Settings page or scripts/reset_admin_password.py for that).

Skipped when MEM0_ADMIN_EMAIL or MEM0_ADMIN_PASSWORD is empty, which restores
upstream's browser setup wizard.
"""

from __future__ import annotations

import os
import sys

from pydantic import BaseModel, EmailStr, ValidationError
from sqlalchemy import func, select

from auth import hash_password
from db import SessionLocal
from models import User

MIN_PASSWORD_LENGTH = 8  # same rule as upstream routers/auth.py


class AdminInput(BaseModel):
    email: EmailStr
    name: str


def main() -> None:
    email = os.environ.get("MEM0_ADMIN_EMAIL", "").strip()
    password = os.environ.get("MEM0_ADMIN_PASSWORD", "")
    name = os.environ.get("MEM0_ADMIN_NAME", "").strip() or "Admin"

    if not email or not password:
        print("bootstrap_admin: MEM0_ADMIN_EMAIL/MEM0_ADMIN_PASSWORD not set; first visitor runs the setup wizard", flush=True)
        return
    if len(password) < MIN_PASSWORD_LENGTH:
        sys.exit(f"bootstrap_admin: MEM0_ADMIN_PASSWORD must be at least {MIN_PASSWORD_LENGTH} characters")
    try:
        admin = AdminInput(email=email, name=name)
    except ValidationError as exc:
        sys.exit(f"bootstrap_admin: invalid MEM0_ADMIN_EMAIL: {exc.errors()[0]['msg']}")

    with SessionLocal() as db:
        if db.scalar(select(func.count(User.id))) > 0:
            print("bootstrap_admin: a user already exists; nothing to do", flush=True)
            return
        db.add(User(name=admin.name, email=str(admin.email), password_hash=hash_password(password), role="admin"))
        db.commit()
        print(f"bootstrap_admin: created admin {admin.email}", flush=True)


if __name__ == "__main__":
    main()
