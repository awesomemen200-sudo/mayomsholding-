"""
create_admin.py
----------------
Run this once to create your first admin login.

    python create_admin.py
"""

import getpass
from database import init_db
from models import Admin

if __name__ == "__main__":
    init_db()

    print("=== Create Mayom Holdings admin account ===")
    username = input("Username: ").strip()
    email = input("Email: ").strip()
    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm password: ")

    if password != confirm:
        print("Passwords do not match. Try again.")
        raise SystemExit(1)

    if len(password) < 8:
        print("Password should be at least 8 characters.")
        raise SystemExit(1)

    if Admin.create(username, email, password):
        print(f"Admin '{username}' created successfully. You can now log in at /login.")
    else:
        print("Could not create admin — username or email may already be in use.")