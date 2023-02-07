from email.utils import parseaddr

import passlib
from fastapi import HTTPException
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing_extensions import Literal

from ..database import SessionLocal
from . import user_models, user_schemas

password_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def get_user(db: Session, user_id: int):
    """
    This function takes a database session and a user ID, and returns the user with that ID.

    Arguments:

    * `db`: Session = Depends(get_db)
    * `user_id`: int

    Returns:

    The first user in the database with the id of user_id
    """

    return db.query(user_models.User).filter(user_models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str):
    """
    If the username exists in the database, return the user object, otherwise return False.
    </code>

    Arguments:

    * `db`: Session = This is the database session that is passed in from the main.py file.
    * `username`: str

    Returns:

    The first record in the database that matches the username.
    """

    if check_records := (
        db.query(user_models.User).filter(user_models.User.username == username).first()
    ):
        return check_records
    return False


def hash_password(password):
    """
    It takes a password as input, and returns a hash of that password

    Arguments:

    * `password`: The password to be hashed.

    Returns:

    The password_context.hash(password) is being returned.
    """

    return password_context.hash(password)


def verify_password(raw_password, hashed_password):
    """
    It takes a raw password and a hashed password and returns True if the raw password matches the
    hashed password

    Arguments:

    * `raw_password`: The password in plain text provided by the user to your application.
    * `hashed_password`: The hashed password that was stored in the database.

    Returns:

    the result of the verify function.
    """

    return password_context.verify(raw_password, hashed_password)


def get_users(db: Session, skip: int = 0, limit: int = 100):
    """
    It returns a list of users from the database, skipping the first `skip` users and limiting the
    result to `limit` users

    Arguments:

    * `db`: Session - this is the database session that we created in the previous step.
    * `skip`: The number of records to skip.
    * `limit`: The maximum number of items to return.

    Returns:

    A list of users
    """

    return db.query(user_models.User).offset(skip).limit(limit).all()


def check_email(email: str):
    """
    It returns the email if it's valid, otherwise it returns False

    Arguments:

    * `email`: str

    Returns:

    The email address if it is valid, otherwise False.
    """

    return email if parseaddr(email)[1] else False


def create_user(db: Session, user: user_schemas.UserCreate):
    """
    It takes a database session, a user object, checks the email, hashes the password, checks if the
    username exists, and if not, creates a new user

    Arguments:

    * `db`: Session = database session
    * `user`: user_schemas.UserCreate

    Returns:

    The user object
    """
    email: str = check_email(user.email)
    hashed_password: str = hash_password(user.password)
    if get_user_by_username(db, user.username):
        raise HTTPException(
            status_code=400, detail="User with this username already exists"
        )

    db_user = user_models.User(
        email=email, hashed_password=hashed_password, username=user.username
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_db():
    """
    It creates a database connection and returns it to the caller.
    """

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
