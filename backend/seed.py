"""
Seeds a demo admin account so the app can be logged into immediately.

Run:  python seed.py
"""
from app.database.db import users_collection
from app.core.security import hash_password

DEMO_USER = {
    "name": "Bindu",
    "email": "admin@greenai.io",
    "password": hash_password("GreenAI@123"),
    "role": "admin",
}


def seed():
    if users_collection().find_one({"email": DEMO_USER["email"]}):
        print(f"Demo user already exists: {DEMO_USER['email']}")
        return
    users_collection().insert_one(DEMO_USER)
    print("Seeded demo user:")
    print(f"  email:    {DEMO_USER['email']}")
    print(f"  password: GreenAI@123")


if __name__ == "__main__":
    seed()
