# main.py
from fastapi import FastAPI, HTTPException, Header, File, UploadFile, Cookie, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from typing import Optional
from pydantic import BaseModel
import uvicorn
import os

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

# Models
class Resource(BaseModel):
    name: str
    description: str
    category: str
    status: str

# Mock bearer token
BEARER_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.mock-token-for-authentication"

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

# 6. Authentication with Cookie and Token
@app.get("/api/authenticated")
async def authenticated(
    authorization: str = Header(...),
    x_custom_token: str = Header(...),
    session_id: Optional[str] = Cookie(None)
):
    # Verify bearer token
    if not authorization.startswith("Bearer ") or authorization.split()[1] != BEARER_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid bearer token")

    # Verify custom token
    if x_custom_token != "custom-security-token":
        raise HTTPException(status_code=401, detail="Invalid custom token")

    # Verify cookie
    if not session_id:
        raise HTTPException(status_code=401, detail="Session cookie required")

    return {
        "message": "Successfully authenticated",
        "user": {
            "id": "user123",
            "role": "admin"
        }
    }

# Health check endpoint for Render
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)