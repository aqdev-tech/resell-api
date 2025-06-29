from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, Integer, String, Enum, Float, Boolean, Text
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from passlib.context import CryptContext
from pydantic import BaseModel
from typing import List, Optional
import enum
import os
import shutil
from jose import JWTError, jwt
from datetime import datetime, timedelta

# --- Configuration ---
DATABASE_URL = "sqlite:///./reselling.db"
SECRET_KEY = "a_very_secret_key_that_should_be_in_env_vars"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- SQLAlchemy Setup ---
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Security ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/admin/login")

# --- Enums ---
class GadgetCondition(str, enum.Enum):
    NEW = "new"
    USED = "used"
    OPEN_BOX = "open_box"

class GadgetType(str, enum.Enum):
    PHONE = "phone"
    LAPTOP = "laptop"
    OTHER = "other"

class ListingStatus(str, enum.Enum):
    PENDING = "pending"
    AVAILABLE = "available"
    SOLD = "sold"
    DELETED = "deleted" # Soft delete

# --- Database Models ---
class GadgetListing(Base):
    __tablename__ = "gadgets"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    gadget_type = Column(Enum(GadgetType))
    condition = Column(Enum(GadgetCondition))
    description = Column(Text)
    seller_price = Column(Float)
    listing_price = Column(Float, nullable=True)
    seller_contact_info = Column(String)
    status = Column(Enum(ListingStatus), default=ListingStatus.PENDING)
    photo_url = Column(String)

class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

class BuyerQuestion(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    question = Column(String)
    contact_info = Column(String)

class GadgetRequest(Base):
    __tablename__ = "gadget_requests"
    id = Column(Integer, primary_key=True, index=True)
    gadget_details = Column(String)
    contact_info = Column(String)
    is_resolved = Column(Boolean, default=False)

class Setting(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(Text)

Base.metadata.create_all(bind=engine)

# --- Pydantic Schemas ---
class GadgetUpdate(BaseModel):
    name: Optional[str] = None
    gadget_type: Optional[GadgetType] = None
    condition: Optional[GadgetCondition] = None
    description: Optional[str] = None
    seller_price: Optional[float] = None
    listing_price: Optional[float] = None


class GadgetRequestSubmission(BaseModel):
    gadget_details: str
    contact_info: str


class GadgetRequestOut(BaseModel):
    id: int
    gadget_details: str
    contact_info: str
    is_resolved: bool

    class Config:
        from_attributes = True


class BulkAction(BaseModel):
    action: ListingStatus
    listing_ids: List[int]



class StatusUpdate(BaseModel):
    status: ListingStatus

class BuyerQuestionSubmission(BaseModel):
    question: str
    contact_info: str

class BuyerQuestionOut(BaseModel):
    id: int
    question: str
    contact_info: str
    class Config:
        from_attributes = True

class Gadget(BaseModel):
    id: int
    name: str
    gadget_type: GadgetType
    condition: GadgetCondition
    description: str
    seller_price: float
    listing_price: Optional[float] = None
    photo_url: str
    status: ListingStatus
    seller_contact_info: str
    class Config:
        from_attributes = True

class PublicGadget(BaseModel):
    id: int
    name: str
    gadget_type: GadgetType
    condition: GadgetCondition
    description: str
    listing_price: float
    photo_url: str
    status: ListingStatus
    admin_whatsapp_number: Optional[str] = None
    class Config:
        from_attributes = True

class AdminDashboard(BaseModel):
    pending_listings: List[Gadget]
    active_listings: List[Gadget]
    sold_listings: List[Gadget]
    buyer_questions: List[BuyerQuestionOut]
    gadget_requests: List[GadgetRequestOut]

class AdminSettings(BaseModel):
    whatsapp_number: str

class Token(BaseModel):
    access_token: str
    token_type: str

    class Config:
        from_attributes = True

# --- Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Utility Functions ---
def get_password_hash(password):
    """Hashes a password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    admin = db.query(Admin).filter(Admin.username == username).first()
    if admin is None:
        raise credentials_exception
    return admin

def get_admin_whatsapp(db: Session):
    setting = db.query(Setting).filter(Setting.key == "whatsapp_number").first()
    return setting.value if setting else None

# --- FastAPI App ---
app = FastAPI(title="Reselling Platform API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# --- API Endpoints ---
@app.post("/seller/submit", response_model=Gadget)
async def submit_gadget(
    name: str,
    gadget_type: GadgetType,
    condition: GadgetCondition,
    description: str,
    seller_price: float,
    seller_contact_info: str,
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    file_path = os.path.join(UPLOAD_DIR, photo.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(photo.file, buffer)

    gadget_data = {
        "name": name,
        "gadget_type": gadget_type,
        "condition": condition,
        "description": description,
        "seller_price": seller_price,
        "seller_contact_info": seller_contact_info,
        "photo_url": f"/uploads/{photo.filename}",
        "status": ListingStatus.PENDING,
    }

    db_gadget = GadgetListing(**gadget_data)
    db.add(db_gadget)
    db.commit()
    db.refresh(db_gadget)
    return db_gadget

@app.post("/admin/login", response_model=Token)
async def admin_login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.username == form_data.username).first()
    if not admin or not verify_password(form_data.password, admin.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    
    access_token = create_access_token(
        data={"sub": admin.username}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/admin/add", response_model=Gadget)
async def add_listing(
    name: str,
    gadget_type: GadgetType,
    condition: GadgetCondition,
    description: str,
    seller_price: float,
    listing_price: float,
    seller_contact_info: str,
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    file_path = os.path.join(UPLOAD_DIR, photo.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(photo.file, buffer)

    gadget_data = {
        "name": name,
        "gadget_type": gadget_type,
        "condition": condition,
        "description": description,
        "seller_price": seller_price,
        "listing_price": listing_price,
        "seller_contact_info": seller_contact_info,
        "photo_url": f"/uploads/{photo.filename}",
        "status": ListingStatus.AVAILABLE,
    }

    db_gadget = GadgetListing(**gadget_data)
    db.add(db_gadget)
    db.commit()
    db.refresh(db_gadget)
    return db_gadget

@app.get("/admin/dashboard", response_model=AdminDashboard)
async def get_dashboard_data(db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    return {
        "pending_listings": db.query(GadgetListing).filter(GadgetListing.status == ListingStatus.PENDING).all(),
        "active_listings": db.query(GadgetListing).filter(GadgetListing.status == ListingStatus.AVAILABLE).all(),
        "sold_listings": db.query(GadgetListing).filter(GadgetListing.status == ListingStatus.SOLD).all(),
        "buyer_questions": db.query(BuyerQuestion).all(),
        "gadget_requests": db.query(GadgetRequest).all()
    }

@app.put("/admin/listings/{listing_id}", response_model=Gadget)
async def update_listing_details(
    listing_id: int, update_data: GadgetUpdate,
    db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)
):
    db_listing = db.query(GadgetListing).filter(GadgetListing.id == listing_id).first()
    if not db_listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(db_listing, key, value)
    
    db.commit()
    db.refresh(db_listing)
    return db_listing

@app.patch("/admin/listings/{listing_id}/status", response_model=Gadget)
async def update_listing_status(
    listing_id: int, status_update: StatusUpdate,
    db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)
):
    db_listing = db.query(GadgetListing).filter(GadgetListing.id == listing_id).first()
    if not db_listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    # Allow restoring a soft-deleted listing
    if db_listing.status == ListingStatus.DELETED and status_update.status in [ListingStatus.AVAILABLE, ListingStatus.PENDING]:
        db_listing.status = status_update.status
    # If rejecting a pending submission, soft delete it instead of hard delete
    elif db_listing.status == ListingStatus.PENDING and status_update.status == ListingStatus.DELETED:
        db_listing.status = ListingStatus.DELETED
    else:
        db_listing.status = status_update.status

    db.commit()
    db.refresh(db_listing)
    return db_listing

@app.post("/admin/settings")
async def update_settings(settings: AdminSettings, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    whatsapp_setting = db.query(Setting).filter(Setting.key == "whatsapp_number").first()
    if whatsapp_setting:
        whatsapp_setting.value = settings.whatsapp_number
    else:
        whatsapp_setting = Setting(key="whatsapp_number", value=settings.whatsapp_number)
        db.add(whatsapp_setting)
    db.commit()
    return {"status": "settings updated", "whatsapp_number": settings.whatsapp_number}

@app.post("/buyer/request", response_model=GadgetRequestOut)
async def submit_gadget_request(
    request: GadgetRequestSubmission, db: Session = Depends(get_db)
):
    db_request = GadgetRequest(**request.dict())
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request


@app.post("/buyer/question")
async def submit_question(question: BuyerQuestionSubmission, db: Session = Depends(get_db)):
    db.add(BuyerQuestion(**question.dict()))
    db.commit()
    return {"status": "question submitted"}

@app.delete("/admin/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    question = (
        db.query(BuyerQuestion).filter(BuyerQuestion.id == question_id).first()
    )
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    db.delete(question)
    db.commit()
    return


@app.get("/listings", response_model=List[PublicGadget])
async def get_public_listings(
    db: Session = Depends(get_db),
    gadget_type: Optional[GadgetType] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    condition: Optional[GadgetCondition] = None,
):
    query = db.query(GadgetListing).filter(
        GadgetListing.status == ListingStatus.AVAILABLE,
        GadgetListing.listing_price.isnot(None)
    )

    if gadget_type:
        query = query.filter(GadgetListing.gadget_type == gadget_type)
    if price_min is not None:
        query = query.filter(GadgetListing.listing_price >= price_min)
    if price_max is not None:
        query = query.filter(GadgetListing.listing_price <= price_max)
    if condition:
        query = query.filter(GadgetListing.condition == condition)

    gadgets = query.order_by(GadgetListing.id.desc()).all()
    admin_whatsapp = get_admin_whatsapp(db)
    
    response = []
    for gadget in gadgets:
        public_gadget = PublicGadget.from_orm(gadget)
        public_gadget.admin_whatsapp_number = admin_whatsapp
        response.append(public_gadget)
        
    return response

@app.get("/listings/approved", response_model=List[PublicGadget])
async def get_approved_listings(db: Session = Depends(get_db)):
    query = db.query(GadgetListing).filter(
        GadgetListing.status == ListingStatus.AVAILABLE,
        GadgetListing.listing_price.isnot(None)
    )

    gadgets = query.order_by(GadgetListing.id.desc()).all()
    admin_whatsapp = get_admin_whatsapp(db)
    
    response = []
    for gadget in gadgets:
        public_gadget = PublicGadget.from_orm(gadget)
        public_gadget.admin_whatsapp_number = admin_whatsapp
        response.append(public_gadget)
        
    return response


@app.get("/uploads/{filename}")
async def get_upload(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)

@app.get("/admin/listings/pending", response_model=List[Gadget])
async def get_pending_listings(db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
   
    return db.query(GadgetListing).filter(GadgetListing.status == ListingStatus.PENDING).all()


@app.post("/admin/listings/bulk", status_code=status.HTTP_200_OK)
async def bulk_update_listings(
    bulk_action: BulkAction,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    if bulk_action.action not in [
        ListingStatus.AVAILABLE,
        ListingStatus.DELETED,
        ListingStatus.SOLD,
    ]:
        raise HTTPException(
            status_code=400,
            detail="Invalid bulk action. Must be 'available', 'deleted', or 'sold'.",
        )

    listings = db.query(GadgetListing).filter(
        GadgetListing.id.in_(bulk_action.listing_ids)
    )
    if not listings.count():
        raise HTTPException(status_code=404, detail="No listings found for the given IDs.")

    for listing in listings:
        listing.status = bulk_action.action

    db.commit()
    return {"status": f"updated {listings.count()} listings to {bulk_action.action.value}"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)