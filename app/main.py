from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.database import engine, get_db, Base  # Add Base to the import
from app.models import user as models
from app.routers import auth, users, crypto, weather

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(crypto.router)
app.include_router(weather.router)  # Remove the duplicate line

@app.get("/")
def read_root():
    return {"message": "Welcome to the Authentication API"}

@app.get("/test-db")
def test_db(db: Session = Depends(get_db)):
    try:
        # Try to create all tables
        Base.metadata.create_all(bind=engine)
        return {"message": "Database connection successful"}
    except Exception as e:
        return {"error": f"Database connection failed: {str(e)}"}