"""
AERO RECON-3D — FastAPI Backend Main Entry Point
"""
import uuid
import asyncio
import traceback
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi.security import OAuth2PasswordRequestForm
from .core.auth import get_password_hash, verify_password, create_access_token, get_current_user
from .db.models import User as DBUser

from .core.config import UPLOADS_DIR, OUTPUTS_DIR
from .pipeline.runner import run_pipeline
from .db.database import engine, Base, get_db, SessionLocal
from .db.models import Job as DBJob, Project as DBProject

# ── App ──────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AeroRecon 3D — Reconstruction API",
    version="0.1.0-milestone1",
    description="Phase 2 Milestone 1: Video → Point Cloud Pipeline (SQLite Persistence)",
)

import os

CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:4173,http://localhost:5173,http://127.0.0.1:4173,http://127.0.0.1:5173")
origins = [origin.strip() for origin in CORS_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Database Initialization ──────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

@app.on_event("startup")
def on_startup():
    db = SessionLocal()
    try:
        # Safe Idempotent SQLite Schema Migrations FIRST before any ORM queries
        try:
            db.execute(text("ALTER TABLE jobs ADD COLUMN report_path VARCHAR"))
            db.commit()
        except Exception:
            db.rollback() # Column likely exists
            
        try:
            db.execute(text("ALTER TABLE jobs ADD COLUMN report_generated_at DATETIME"))
            db.commit()
        except Exception:
            db.rollback()

        # Phase C Migration: Normalize existing user emails safely
        try:
            db.execute(text("UPDATE users SET email = LOWER(TRIM(email)) WHERE email != LOWER(TRIM(email))"))
            db.commit()
        except Exception:
            db.rollback()

        # Restart Behavior: Mark orphaned RUNNING jobs as FAILED
        running_jobs = db.query(DBJob).filter(DBJob.status == "RUNNING").all()
        for job in running_jobs:
            job.status = "FAILED"
            job.progress = "Pipeline failed"
            job.error = "Backend stopped unexpectedly before completion."
        if running_jobs:
            db.commit()
            
    finally:
        db.close()

# ── Models ────────────────────────────────────────────────────────────────
class JobStatus(BaseModel):
    job_id: str
    project_id: Optional[str] = None
    status: str          # QUEUED | RUNNING | SUCCESS | FAILED | UPLOADED
    progress: str
    current_stage: Optional[str] = None
    stage_progress: Optional[int] = None
    telemetry_path: Optional[str] = None
    ply_path: Optional[str] = None
    preview_ply_path: Optional[str] = None
    point_count: Optional[int] = None
    elapsed_seconds: Optional[float] = None
    error: Optional[str] = None

class JobSummary(BaseModel):
    job_id: str
    project_id: Optional[str] = None
    status: str
    progress: str
    current_stage: Optional[str] = None
    stage_progress: Optional[int] = None
    point_count: Optional[int] = None
    elapsed_seconds: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # UI-safe derived fields
    video_filename: Optional[str] = None
    has_telemetry: bool = False
    has_metric_alignment: bool = False
    coordinate_system: str = "LOCAL / RELATIVE"
    has_ply: bool = False
    has_glb: bool = False
    
    class Config:
        from_attributes = True

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# ── Background job runner ─────────────────────────────────────────────────
def _run_job(job_id: str, video_path: Path):
    db = SessionLocal()
    try:
        job = db.query(DBJob).filter(DBJob.job_id == job_id).first()
        if not job:
            return
            
        job.status = "RUNNING"
        job.progress = "Pipeline started"
        job.current_stage = "Initializing"
        job.stage_progress = 0
        db.commit()

        def on_progress(stage: str, prog: int):
            if job.status != "FAILED":
                job.current_stage = stage
                job.stage_progress = prog
                job.progress = f"Running: {stage}"
                db.commit()

        result = run_pipeline(video_path, job_id, on_progress=on_progress)
        
        job.status = result["status"]
        job.progress = "Pipeline complete" if result["status"] == "SUCCESS" else "Pipeline failed"
        if result["status"] == "SUCCESS":
            job.current_stage = "Complete"
        job.stage_progress = 100 if result["status"] == "SUCCESS" else (job.stage_progress or 0)
        job.ply_path = result.get("ply_path")
        job.preview_ply_path = result.get("preview_ply_path")
        job.point_count = result.get("point_count")
        job.elapsed_seconds = result.get("total_elapsed_seconds")
        
        db.commit()
    except Exception as exc:
        tb = traceback.format_exc()
        db.rollback()
        job = db.query(DBJob).filter(DBJob.job_id == job_id).first()
        if job:
            job.status = "FAILED"
            job.progress = "Exception in pipeline"
            job.error = str(exc)
            job.traceback = tb
            db.commit()
    finally:
        db.close()


# ── Routes ────────────────────────────────────────────────────────────────
@app.get("/", tags=["health"])
async def root():
    return {"service": "AeroRecon3D Backend", "version": "0.1.0-milestone1", "status": "ok"}

@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}


@app.post("/projects", tags=["projects"], response_model=ProjectResponse)
async def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    db_proj = DBProject(id=uuid.uuid4().hex[:8], name=project.name, description=project.description)
    db.add(db_proj)
    db.commit()
    db.refresh(db_proj)
    return db_proj

@app.get("/projects", tags=["projects"], response_model=List[ProjectResponse])
async def list_projects(db: Session = Depends(get_db)):
    return db.query(DBProject).all()

@app.get("/projects/{project_id}", tags=["projects"], response_model=ProjectResponse)
async def get_project(project_id: str, db: Session = Depends(get_db)):
    proj = db.query(DBProject).filter(DBProject.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return proj


@app.post("/upload", tags=["pipeline"], response_model=JobStatus)
async def upload_video(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...),
    telemetry_file: Optional[UploadFile] = File(None),
    project_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Upload a drone video and start the reconstruction pipeline."""
    job_id = uuid.uuid4().hex[:8]
    ext = Path(file.filename or "video.mp4").suffix.lower()
    if ext not in (".mp4", ".avi", ".mov", ".mkv", ".m4v", ".webm"):
        raise HTTPException(status_code=400, detail=f"Unsupported video format: {ext}")
        
    if project_id:
        proj = db.query(DBProject).filter(DBProject.id == project_id).first()
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found")

    upload_path = UPLOADS_DIR / f"{job_id}{ext}"
    with open(upload_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):  # 1 MB chunks
            f.write(chunk)
            
    telemetry_path_str = None
    if telemetry_file:
        tel_ext = Path(telemetry_file.filename or "").suffix.lower()
        if tel_ext in (".srt", ".csv", ".json"):
            tel_path = UPLOADS_DIR / f"{job_id}_telemetry{tel_ext}"
            with open(tel_path, "wb") as f:
                while chunk := await telemetry_file.read(1024 * 1024):
                    f.write(chunk)
            telemetry_path_str = str(tel_path)

    db_job = DBJob(
        job_id=job_id,
        project_id=project_id,
        status="UPLOADED",
        progress="Video uploaded — ready to start",
        upload_path=str(upload_path),
        telemetry_path=telemetry_path_str
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)

    return JobStatus(**{k: getattr(db_job, k) for k in JobStatus.model_fields if hasattr(db_job, k)})


@app.post("/start/{job_id}", tags=["pipeline"], response_model=JobStatus)
async def start_pipeline(job_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Start the reconstruction pipeline for an uploaded video."""
    db_job = db.query(DBJob).filter(DBJob.job_id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if db_job.status in ("RUNNING", "SUCCESS"):
        raise HTTPException(status_code=400, detail=f"Job already {db_job.status}")
        
    upload_path = db_job.upload_path
    if not upload_path or not Path(upload_path).exists():
        raise HTTPException(status_code=404, detail="Video file not found on server")

    background_tasks.add_task(_run_job, job_id, Path(upload_path))
    
    db_job.status = "QUEUED"
    db_job.progress = "Pipeline queued for execution"
    db.commit()
    
    return JobStatus(**{k: getattr(db_job, k) for k in JobStatus.model_fields if hasattr(db_job, k)})


@app.get("/status/{job_id}", tags=["pipeline"], response_model=JobStatus)
async def job_status(job_id: str, db: Session = Depends(get_db)):
    """Poll reconstruction job status."""
    db_job = db.query(DBJob).filter(DBJob.job_id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatus(**{k: getattr(db_job, k) for k in JobStatus.model_fields if hasattr(db_job, k)})

@app.get("/jobs", tags=["pipeline"], response_model=List[JobSummary])
async def list_jobs(db: Session = Depends(get_db)):
    """Get all recent jobs with secure UI-only summaries."""
    db_jobs = db.query(DBJob).order_by(DBJob.created_at.desc()).limit(50).all()
    summaries = []
    
    for db_job in db_jobs:
        # Derive secure fields without exposing paths
        video_filename = Path(db_job.upload_path).name if db_job.upload_path else "Unknown Video"
        has_tel = bool(db_job.telemetry_path)
        has_ply = bool(db_job.ply_path)
        
        # Check GLB
        stage7_dir = OUTPUTS_DIR / db_job.job_id / "stage7"
        has_glb = (stage7_dir / "textured_model_safe.glb").exists() or (stage7_dir / "textured_model_web.glb").exists()
        
        summary = JobSummary(
            job_id=db_job.job_id,
            project_id=db_job.project_id,
            status=db_job.status,
            progress=db_job.progress,
            current_stage=db_job.current_stage,
            stage_progress=db_job.stage_progress,
            point_count=db_job.point_count,
            elapsed_seconds=db_job.elapsed_seconds,
            created_at=db_job.created_at,
            updated_at=db_job.updated_at,
            video_filename=video_filename,
            has_telemetry=has_tel,
            has_metric_alignment=False,  # Strict fallback as per honesty requirements
            coordinate_system="LOCAL / RELATIVE",
            has_ply=has_ply,
            has_glb=has_glb
        )
        summaries.append(summary)
        
    return summaries


@app.get("/download/{job_id}/ply", tags=["pipeline"])
async def download_ply(job_id: str, db: Session = Depends(get_db)):
    """Download the generated .PLY point cloud file."""
    db_job = db.query(DBJob).filter(DBJob.job_id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
    if db_job.status != "SUCCESS":
        raise HTTPException(status_code=400, detail=f"Job not complete (status: {db_job.status})")
    
    ply = db_job.ply_path
    if not ply or not Path(ply).exists():
        raise HTTPException(status_code=404, detail="PLY file not found")
    return FileResponse(
        path=ply,
        filename=f"aerorecon_{job_id}.ply",
        media_type="application/octet-stream",
    )


@app.get("/download/{job_id}/preview", tags=["pipeline"])
async def download_preview(job_id: str, db: Session = Depends(get_db)):
    """Download the downsampled preview PLY point cloud file."""
    db_job = db.query(DBJob).filter(DBJob.job_id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
    if db_job.status != "SUCCESS":
        raise HTTPException(status_code=400, detail=f"Job not complete (status: {db_job.status})")
    
    preview = db_job.preview_ply_path
    ply = db_job.ply_path
    target_path = preview if (preview and Path(preview).exists()) else ply
    
    if not target_path or not Path(target_path).exists():
        raise HTTPException(status_code=404, detail="Preview PLY file not found")
        
    return FileResponse(
        path=target_path,
        filename=f"aerorecon_{job_id}_preview.ply",
        media_type="application/octet-stream",
    )

@app.get("/download/{job_id}/glb", tags=["pipeline"])
async def download_glb(job_id: str, db: Session = Depends(get_db)):
    """Download the generated vertex-colored GLB file."""
    db_job = db.query(DBJob).filter(DBJob.job_id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
    if db_job.status != "SUCCESS":
        raise HTTPException(status_code=400, detail=f"Job not complete (status: {db_job.status})")
    
    stage7_dir = OUTPUTS_DIR / job_id / "stage7"
    web_glb = stage7_dir / "textured_model_web.glb"
    high_glb = stage7_dir / "textured_model_high.glb"
    
    target_path = web_glb if web_glb.exists() else (high_glb if high_glb.exists() else None)
    
    if not target_path:
        raise HTTPException(status_code=404, detail="GLB model not found")
        
    return FileResponse(
        path=str(target_path),
        filename=f"aerorecon_{job_id}_model.glb",
        media_type="model/gltf-binary",
    )


@app.get("/report/{job_id}", tags=["pipeline"])
async def download_report(job_id: str):
    """Download the full pipeline JSON report."""
    report_path = OUTPUTS_DIR / job_id / "pipeline_report.json"
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(
        path=str(report_path),
        filename=f"report_{job_id}.json",
        media_type="application/json",
    )


@app.get("/jobs", tags=["pipeline"])
async def list_jobs(db: Session = Depends(get_db)):
    """List all known jobs and their statuses."""
    jobs = db.query(DBJob).all()
    return [
        {"job_id": j.job_id, "status": j.status, "progress": j.progress}
        for j in jobs
    ]
from pydantic import BaseModel

class ReportResponse(BaseModel):
    job_id: str
    generated: bool
    generated_at: Optional[datetime] = None
    available: bool

# ── Report Endpoints ──────────────────────────────────────────────────────

@app.post("/reports/{job_id}/generate", tags=["reports"], response_model=ReportResponse)
async def generate_report_api(job_id: str, db: Session = Depends(get_db)):
    from .reports.generator import generate_report
    
    job = db.query(DBJob).filter(DBJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if job.status != "SUCCESS" and job.status != "FAILED":
        raise HTTPException(status_code=400, detail="Job is not completed yet")
        
    try:
        report_dir = OUTPUTS_DIR / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        
        pdf_path = generate_report(job, str(report_dir))
        
        job.report_path = pdf_path
        job.report_generated_at = datetime.utcnow()
        db.commit()
        
        return ReportResponse(
            job_id=job.job_id,
            generated=True,
            generated_at=job.report_generated_at,
            available=True
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")

@app.get("/reports/{job_id}", tags=["reports"], response_model=ReportResponse)
async def get_report_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(DBJob).filter(DBJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if not job.report_path:
        raise HTTPException(status_code=404, detail="Report not generated")
        
    return ReportResponse(
        job_id=job.job_id,
        generated=True,
        generated_at=job.report_generated_at,
        available=True
    )

@app.get("/reports/{job_id}/download", tags=["reports"])
async def download_report(job_id: str, db: Session = Depends(get_db)):
    job = db.query(DBJob).filter(DBJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if not job.report_path or not Path(job.report_path).exists():
        raise HTTPException(status_code=404, detail="Report file not found on disk")
        
    return FileResponse(
        path=job.report_path,
        filename=f"aerorecon_{job_id}_report.pdf",
        media_type="application/pdf"
    )
# ── Auth Endpoints ────────────────────────────────────────────────────────

from pydantic import EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

@app.post("/auth/register", tags=["auth"], response_model=Token, status_code=201)
async def register(user_in: UserCreate, db: Session = Depends(get_db)):
    if len(user_in.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    normalized_email = user_in.email.strip().lower()
    
    # Check duplicate
    existing = db.query(DBUser).filter(DBUser.email == normalized_email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
        
    hashed_pw = get_password_hash(user_in.password)
    user_id = uuid.uuid4().hex
    
    new_user = DBUser(
        id=user_id,
        email=normalized_email,
        password_hash=hashed_pw,
        is_active=1
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token = create_access_token(data={"sub": new_user.id, "email": new_user.email})
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(id=new_user.id, email=new_user.email)
    )

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/auth/login", tags=["auth"], response_model=Token)
async def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    normalized_email = credentials.email.strip().lower()
    user = db.query(DBUser).filter(DBUser.email == normalized_email).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
        
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    access_token = create_access_token(data={"sub": user.id, "email": user.email})
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(id=user.id, email=user.email)
    )

@app.get("/auth/me", tags=["auth"], response_model=UserResponse)
async def read_users_me(current_user: DBUser = Depends(get_current_user)):
    return UserResponse(id=current_user.id, email=current_user.email)
