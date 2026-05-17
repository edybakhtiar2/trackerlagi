from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session
import datetime

# ==========================================
# 1. SETUP DATABASE SQLITE
# ==========================================
SQLALCHEMY_DATABASE_URL = "postgresql://neondb_owner:npg_q91fhVloIOZi@ep-silent-glitter-aord7xmk-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Membuat struktur tabel 'locations' di database
class LocationDB(Base):
    __tablename__ = "locations"
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

# Perintah ini akan otomatis membuat file database.db jika belum ada
Base.metadata.create_all(bind=engine)

# ==========================================
# 2. INISIALISASI FASTAPI & KEAMANAN
# ==========================================
app = FastAPI(title="GPS Tracking API")

# Mengizinkan Web Dashboard (CORS) untuk mengambil data dari API ini
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True, 
    allow_methods=["*"],
    allow_headers=["*"],
)

# Struktur data JSON yang diharapkan dari aplikasi Android/Client
class LocationPayload(BaseModel):
    device_id: str
    latitude: float
    longitude: float
    secret_token: str # Token sederhana untuk keamanan

# Fungsi bantuan untuk membuka dan menutup koneksi database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# 3. ENDPOINT API (RUTE)
# ==========================================

# Endpoint A: Menerima data lokasi dari HP (POST)
@app.post("/api/location")
def update_location(payload: LocationPayload, db: Session = Depends(get_db)):
    # Validasi keamanan dasar
    if payload.secret_token != "TOKEN_RAHASIA_KITA_123":
        raise HTTPException(status_code=401, detail="Akses Ditolak: Token Salah")
    
    # Menyimpan data ke database
    new_loc = LocationDB(
        device_id=payload.device_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        timestamp=datetime.datetime.now()
    )
    db.add(new_loc)
    db.commit()
    
    return {"status": "success", "message": "Lokasi berhasil disimpan"}

# Endpoint B: Mengirim data lokasi terakhir ke Web Dashboard (GET)
@app.get("/api/location/{device_id}")
def get_location(device_id: str, db: Session = Depends(get_db)):
    # Mengambil 1 baris data paling baru berdasarkan waktu (timestamp)
    loc = db.query(LocationDB).filter(LocationDB.device_id == device_id).order_by(LocationDB.timestamp.desc()).first()
    
    if not loc:
        raise HTTPException(status_code=404, detail="Perangkat belum mengirimkan lokasi")
    
    return {
        "device_id": loc.device_id, 
        "lat": loc.latitude, 
        "lng": loc.longitude, 
        "time": loc.timestamp
    }