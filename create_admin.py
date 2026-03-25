import argparse

from api.users.models import User, UserRole
from core.db import SessionLocal
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def parse_args():
    parser = argparse.ArgumentParser(description="Create or promote an admin user.")
    parser.add_argument("--email", required=True, help="Admin email")
    parser.add_argument("--password", help="Required when creating a new user")
    parser.add_argument("--firstname", help="Required when creating a new user")
    parser.add_argument("--lastname", help="Required when creating a new user")
    parser.add_argument("--username", help="Required when creating a new user")
    parser.add_argument("--phone-number", dest="phone_number", help="Required when creating a new user")
    return parser.parse_args()


def main():
    args = parse_args()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == args.email).first()

        if user:
            user.role = UserRole.admin
            db.commit()
            db.refresh(user)
            print(f"Promoted existing user to ADMIN: {user.email}")
            return

        required = {
            "password"    : args.password,
            "firstname"   : args.firstname,
            "lastname"    : args.lastname,
            "username"    : args.username,
            "phone_number": args.phone_number,
        }
        missing = [key for key, value in required.items() if not value]
        if missing:
            missing_text = ", ".join(missing)
            raise ValueError(
                f"Missing required arguments for new admin user: {missing_text}"
            )

        user = User(
            firstname         = args.firstname,
            firstname_lc      = args.firstname.lower(),
            lastname          = args.lastname,
            lastname_lc       = args.lastname.lower(),
            username          = args.username,
            email             = args.email,
            phone_number      = args.phone_number,
            password_hash     = hash_password(args.password),
            role              = UserRole.admin,
            is_verified       = True,
            profile_image_url = None,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Created new ADMIN user: {user.email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
