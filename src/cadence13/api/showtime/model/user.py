from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from cadence13.db.tables import User

pw_hasher = PasswordHasher()


def create_user(session, first_name, last_name, email, password):
    row = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=pw_hasher.hash(password)
    )
    session.add(row)
    session.commit()


def is_password_valid(session, email, password):
    hashed_pw = (session.query(User.password)
                 .filter_by(email=email).scalar())
    if not hashed_pw:
        return False
    try:
        pw_hasher.verify(hashed_pw, password)
        return True
    except VerificationError:
        return False
