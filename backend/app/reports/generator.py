import os
from datetime import datetime
from fpdf import FPDF
from ..db.models import Job

# Standard pipeline stages in order
PIPELINE_STAGES = [
    "Frame Extraction",
    "Feature Tracking",
    "Camera Pose",
    "Depth Estimation",
    "Point Cloud Generation",
    "Reprojection Validation",
    "Mesh Generation",
    "Vertex-Colored GLB Export"
]

class ReportPDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 20)
        self.set_text_color(25, 45, 75)  # Navy blue
        self.cell(0, 10, 'AERO RECON-3D', border=0, new_x='LMARGIN', new_y='NEXT', align='L')
        self.set_font('helvetica', 'I', 12)
        self.set_text_color(50, 150, 200)  # Cyan/Blue
        self.cell(0, 10, 'FROM VIDEO TO REAL-WORLD IMPACT', border=0, new_x='LMARGIN', new_y='NEXT', align='L')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

    def chapter_title(self, title):
        self.set_font('helvetica', 'B', 14)
        self.set_text_color(25, 45, 75)
        self.cell(0, 10, title, border='B', new_x='LMARGIN', new_y='NEXT', align='L')
        self.ln(4)

    def row(self, label, value):
        self.set_font('helvetica', 'B', 11)
        self.set_text_color(50, 50, 50)
        self.cell(60, 8, label + ":", align='L')
        self.set_font('helvetica', '', 11)
        self.set_text_color(0, 0, 0)
        self.cell(0, 8, str(value), new_x='LMARGIN', new_y='NEXT', align='L')

def generate_report(job: Job, output_dir: str) -> str:
    pdf = ReportPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # ------------------------------------------------
    # PROJECT INFORMATION
    # ------------------------------------------------
    pdf.chapter_title('PROJECT INFORMATION')
    pdf.row('Project Name', job.project.name if job.project else 'N/A')
    pdf.row('Project ID', job.project_id if job.project_id else 'N/A')
    pdf.row('Job ID', job.job_id)
    video_filename = os.path.basename(job.upload_path) if job.upload_path else 'N/A'
    pdf.row('Video Filename', video_filename)
    pdf.row('Creation Date', job.created_at.strftime('%Y-%m-%d %H:%M:%S') if job.created_at else 'N/A')
    pdf.row('Processing Status', job.status)
    
    duration = f"{int(job.elapsed_seconds)} seconds" if job.elapsed_seconds else "N/A"
    pdf.row('Processing Duration', duration)
    pdf.ln(5)

    # ------------------------------------------------
    # INPUT INFORMATION
    # ------------------------------------------------
    pdf.chapter_title('INPUT INFORMATION')
    pdf.row('Video Filename', video_filename)
    
    has_telemetry = bool(job.telemetry_path)
    pdf.row('Telemetry Availability', 'AVAILABLE' if has_telemetry else 'UNAVAILABLE')
    pdf.row('Telemetry Source', 'DJI SRT / Custom CSV' if has_telemetry else 'NONE')
    pdf.ln(5)

    # ------------------------------------------------
    # PROCESSING PIPELINE
    # ------------------------------------------------
    pdf.chapter_title('PROCESSING PIPELINE')
    
    current_idx = -1
    if job.current_stage:
        try:
            current_idx = PIPELINE_STAGES.index(job.current_stage)
        except ValueError:
            current_idx = len(PIPELINE_STAGES)
            
    for i, stage in enumerate(PIPELINE_STAGES):
        status = "Not Run"
        if job.status == "SUCCESS":
            status = "Completed"
        elif job.status == "FAILED":
            if i < current_idx:
                status = "Completed"
            elif i == current_idx:
                status = "Failed"
            else:
                status = "Not Run"
        elif job.status == "RUNNING":
            if i < current_idx:
                status = "Completed"
            elif i == current_idx:
                status = "Running"
            else:
                status = "Pending"
        else: # QUEUED / UPLOADED
            status = "Pending"
            
        pdf.row(stage, status)
    pdf.ln(5)

    # ------------------------------------------------
    # MODEL OUTPUT
    # ------------------------------------------------
    pdf.chapter_title('MODEL OUTPUT')
    pdf.row('Point Count', f"{job.point_count:,}" if job.point_count else '0')
    pdf.row('Mesh Availability', 'Completed' if job.status == 'SUCCESS' else 'Unavailable')
    pdf.row('GLB Availability', 'Unavailable (PLY only)' if job.status == 'SUCCESS' else 'Unavailable')
    pdf.row('Coordinate System', 'LOCAL / RELATIVE')
    pdf.row('Metric Alignment Status', 'UNAVAILABLE')
    pdf.ln(5)

    # ------------------------------------------------
    # TELEMETRY
    # ------------------------------------------------
    pdf.chapter_title('TELEMETRY STATUS')
    pdf.row('GPS', 'Available (from telemetry)' if has_telemetry else 'Unavailable')
    pdf.row('IMU', 'Available (from telemetry)' if has_telemetry else 'Unavailable')
    pdf.row('Synchronization Status', 'Completed' if has_telemetry and job.status == 'SUCCESS' else 'Unavailable')
    pdf.row('Metric Alignment Status', 'Unavailable')
    pdf.row('Georeferencing Status', 'Unavailable')
    pdf.ln(5)

    # ------------------------------------------------
    # ACCURACY
    # ------------------------------------------------
    pdf.chapter_title('ACCURACY / VALIDATION')
    pdf.set_font('helvetica', 'I', 11)
    pdf.set_text_color(150, 50, 50)
    pdf.cell(0, 8, 'Metric accuracy unavailable - ground truth reference required.', new_x='LMARGIN', new_y='NEXT', align='L')
    pdf.ln(5)

    # ------------------------------------------------
    # LIMITATIONS
    # ------------------------------------------------
    pdf.chapter_title('LIMITATIONS')
    pdf.set_font('helvetica', '', 11)
    pdf.set_text_color(0, 0, 0)
    
    limitations = []
    if not has_telemetry:
        limitations.append("- GPS/IMU telemetry data unavailable.")
    limitations.append("- Metric scale and ground truth validation unavailable.")
    limitations.append("- Real-world absolute georeferencing unavailable.")
    
    for lim in limitations:
        pdf.cell(0, 8, lim, new_x='LMARGIN', new_y='NEXT', align='L')
    pdf.ln(5)

    # ------------------------------------------------
    # OUTPUT AVAILABILITY
    # ------------------------------------------------
    pdf.chapter_title('OUTPUT AVAILABILITY')
    pdf.row('Point Cloud (PLY)', 'Ready' if job.ply_path else 'Unavailable')
    pdf.row('Preview Model', 'Ready' if job.preview_ply_path else 'Unavailable')
    pdf.row('Mesh (GLB)', 'Unavailable')

    # Save PDF
    os.makedirs(output_dir, exist_ok=True)
    filename = f"aerorecon_{job.job_id}_report.pdf"
    filepath = os.path.join(output_dir, filename)
    pdf.output(filepath)
    
    return filepath
