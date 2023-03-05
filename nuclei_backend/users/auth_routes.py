from datetime import timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from nuclei_backend.users import user_handler_utils
from jose import JWTError, jwt


# import db
from .auth_utils import authenticate_user, create_access_token, get_current_user
from .main import users_router
from .user_models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/token")
from fastapi.param_functions import Form


@users_router.post("/token")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db=Depends(user_handler_utils.get_db),
):
    user = authenticate_user(
        username=form_data.username,
        password=form_data.password,
        db=db,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username},
        expire_delta=access_token_expires,
    )

    return {"access_token": access_token, "token_type": "bearer"}


@users_router.get("/me")
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@users_router.post("/token/verify")
async def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        token_data = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        sub = token_data.get("sub")
        if sub is None:
            raise HTTPException(
                status_code=401, detail="Invalid authentication credentials"
            )
    except JWTError:
        raise HTTPException(
            status_code=401, detail="Invalid authentication credentials"
        )
    return {"status": True}


@users_router.post("/token/refresh")
async def refresh_token(token: str = Depends(oauth2_scheme)):
    try:
        token_data = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        sub = token_data.get("sub")
        if sub is None:
            raise HTTPException(
                status_code=401, detail="Invalid authentication credentials"
            )
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": sub},
            expire_delta=access_token_expires,
        )
    except JWTError:
        raise HTTPException(
            status_code=401, detail="Invalid authentication credentials"
        )
    return JSONResponse({"access_token": access_token})
