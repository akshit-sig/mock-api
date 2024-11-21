# main.py
from fastapi import FastAPI, HTTPException, Header, File, UploadFile, Cookie, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Optional
from pydantic import BaseModel
import uvicorn
import os
import secrets
from jose import jwt
from datetime import datetime, timedelta

# Initialize FastAPI app
app = FastAPI(title="Mock APIs", description="Collection of mock API endpoints")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security scheme for bearer token
security = HTTPBearer()

# Authentication Configuration
SECRET_KEY = secrets.token_hex(32)  # Generates a secure random secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# Models
class Resource(BaseModel):
    name: str
    description: str
    category: str
    status: str


# Authentication Models
class User(BaseModel):
    username: str
    disabled: Optional[bool] = None
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


# OAuth2 Password Bearer for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Simulated user database
fake_users_db = {
    "testuser": {
        "username": "testuser",
        "password": "fakehashedsecret",
        "disabled": False,
    }
}


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create a JWT access token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def fake_hash_password(password: str):
    """
    Simulate password hashing (DO NOT use in production)
    """
    return "fakehashed" + password


def get_user(db, username: str):
    """
    Retrieve user from simulated database
    """
    if username in db:
        user_dict = db[username]
        return User(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
    """
    Authenticate user credentials
    """
    user = get_user(fake_db, username)
    if not user:
        return False

    # Simple password check (replace with proper hashing in production)
    if fake_hash_password(password) != fake_hash_password(user.password):
        return False

    return user


# Original Endpoints

# 1. Internal Server Error (500)
@app.get("/api/error-500")
async def error_500():
    raise HTTPException(
        status_code=500,
        detail={"error": "Internal Server Error", "message": "An unexpected error occurred"}
    )


# 2. Unauthorized Error (401)
@app.get("/api/unauthorized")
async def unauthorized():
    raise HTTPException(
        status_code=401,
        detail={"error": "Unauthorized", "message": "Authentication required"}
    )


# 3. Create Resource (POST - 201)
@app.post("/api/resources", status_code=201)
async def create_resource(resource: Resource):
    return {
        "id": "123",
        "message": "Resource created successfully"
    }


# 4. Update File (PUT - 200)
@app.put("/api/files/upload")
async def upload_file(
        file: UploadFile,
        x_file_type: str = Header(...),
        x_file_password: str = Header(...)
):
    # In a real application, you would process the file here
    return {
        "message": "File uploaded successfully",
        "fileId": "file123",
        "filename": file.filename,
        "file_type": x_file_type
    }


# 5. Cross-Origin Resource
@app.get("/api/cross-origin")
async def cross_origin():
    return {
        "message": "This is a cross-origin enabled endpoint"
    }


# Authentication Endpoints

# Authentication Token Endpoint
@app.post("/token", response_model=Token)
async def login_for_access_token(
        response: Response,
        form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login endpoint
    """
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password"
        )

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    # Set authentication cookie
    response.set_cookie(
        key="auth_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# Protected Endpoint Example
@app.get("/api/protected")
async def read_protected_resource(
        token: str = Depends(oauth2_scheme),
        auth_token: Optional[str] = Cookie(None)
):
    """
    Example of a protected endpoint requiring token authentication
    """
    # Validate the token (in a real app, you'd do more comprehensive validation)
    try:
        # Attempt to decode the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")

        # Additional validation can be added here
        if username is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")

        return {
            "message": "Access to protected resource granted",
            "username": username
        }
    except jwt.JWTError:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials"
        )


# Health check endpoint for Render
@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)