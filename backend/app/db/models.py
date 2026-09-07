from sqlalchemy import Column, String, Float, Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    jobs = relationship("Job", back_populates="project")

class Job(Base):
    __tablename__ = "jobs"
    
    job_id = Column(String, primary_key=True, index=True)
    project_id = Column(String, ForeignKey("projects.id"), index=True, nullable=True)
    
    status = Column(String, index=True, nullable=False, default="UPLOADED")
    progress = Column(String, nullable=False)
    current_stage = Column(String, nullable=True)
    stage_progress = Column(Integer, nullable=True)
    
    upload_path = Column(String, nullable=True)
    telemetry_path = Column(String, nullable=True)
    ply_path = Column(String, nullable=True)
    preview_ply_path = Column(String, nullable=True)
    point_count = Column(Integer, nullable=True)
    elapsed_seconds = Column(Float, nullable=True)
    error = Column(Text, nullable=True)
    traceback = Column(Text, nullable=True)
    
    report_path = Column(String, nullable=True)
    report_generated_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    project = relationship("Project", back_populates="jobs")

