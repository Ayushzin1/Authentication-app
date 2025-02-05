from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, EmailStr
from app.database import get_db
from app.models.user import User
from app.routers.auth import oauth2_scheme, SECRET_KEY, pwd_context, get_current_user  # Add get_current_user
from jose import jwt
from fastapi import Body  # Add this import at the top

# Define the router
router = APIRouter(
    prefix="/users",
    tags=["users"]
)

# Add response model for user profile
class UserProfile(BaseModel):
    email: str
    full_name: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    photo_url: Optional[str] = None
    facebook_id: Optional[str] = None

    class Config:
        from_attributes = True  # This enables ORM model serialization

@router.get("/profile", response_model=UserProfile)
async def get_profile(
    current_user: dict = Depends(get_current_user),  # Changed to use get_current_user
    db: Session = Depends(get_db)
):
    try:
        user = db.query(User).filter(User.email == current_user["email"]).first()
        if not user:
            user = User(
                email=current_user["email"],
                full_name=current_user.get("name"),
                facebook_id=current_user.get("facebook_id")
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        return UserProfile.from_orm(user)
        
    except Exception as e:
        print(f"Profile error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None

@router.put("/profile", response_model=UserProfile)
async def update_profile(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = payload.get("sub")
        
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        for field, value in user_update.dict(exclude_unset=True).items():
            setattr(user, field, value)
        
        db.commit()
        db.refresh(user)
        return user
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

@router.post("/profile/photo", response_model=UserProfile)
async def upload_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = payload.get("sub")
        
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Create uploads directory if it doesn't exist
        import os
        os.makedirs("uploads", exist_ok=True)
        
        # Save file and update user photo_url
        file_location = f"uploads/{file.filename}"
        with open(file_location, "wb+") as file_object:
            file_object.write(await file.read())
        
        user.photo_url = file_location
        db.commit()
        db.refresh(user)
        return user
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str

@router.put("/profile/password")
async def update_password(
    password_data: PasswordUpdate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = payload.get("sub")
        
        user = db.query(User).filter(User.email == email).first()
        if not user or not pwd_context.verify(password_data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )
        
        user.hashed_password = pwd_context.hash(password_data.new_password)
        db.commit()
        return {"message": "Password updated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not update password"
        )

@router.put("/profile/photo-url")
async def update_photo_url(
    photo_url: str = Body(...),  # Changed from query parameter to request body
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = payload.get("sub")
        
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.photo_url = photo_url
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update photo URL"
        )