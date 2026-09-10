import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  Plus, FolderKanban, CheckCircle2, Box, XCircle,
  Video, Navigation, MoreVertical,
  ShieldAlert, Map, Zap, Waypoints, Building2
} from 'lucide-react';
import { cn, formatDate, getStatusLabel } from '../utils';
import { useSettings } from '../contexts/SettingsContext';

import heroSurveyImg from '../assets/hero_survey.webp';
import ucInfrastructureImg from '../assets/uc_infrastructure.webp';
import ucDisasterImg from '../assets/uc_disaster.webp';
import ucUrbanImg from '../assets/uc_urban.webp';
import ucRoadImg from '../assets/uc_road.webp';
import ucEmergencyImg from '../assets/uc_emergency.webp';
import { apiFetch } from '../utils/api';

interface Project {
  id: string;
  name: string;
  description: string;
  created_at: string;
}

interface JobSummary {
  job_id: string;
  project_id: string | null;
  status: string;
  progress: string;
  current_stage: string | null;
  stage_progress: number | null;
  point_count: number | null;
  elapsed_seconds: number | null;
  created_at: string;
  updated_at: string | null;
  video_filename: string;
  has_telemetry: boolean;
  has_ply: boolean;
  has_glb: boolean;
}

const PIPELINE_STEPS = [
  { label: 'Video', stageNames: ['Initializing', 'UPLOADED'] },
  { label: 'Frame Ext.', stageNames: ['Frame Extraction'] },
  { label: 'Feature Track', stageNames: ['Feature Tracking'] },
  { label: 'Camera Pose', stageNames: ['Pose Estimation'] },
  { label: 'Depth', stageNames: ['Depth Estimation'] },
  { label: 'Point Cloud', stageNames: ['Point Cloud'] },
  { label: 'Mesh', stageNames: ['Mesh Generation'] },
  { label: 'GLB', stageNames: ['Vertex-Colored GLB Export'] },
];

export default function Dashboard() {
  const navigate = useNavigate();
  const { settings } = useSettings();
  const [projects, setProjects] = useState<Project[]>([]);
  const [jobs, setJobs] = useState<JobSummary[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [projRes, jobsRes] = await Promise.all([
          apiFetch('/projects').catch(() => null),
          apiFetch('/jobs').catch(() => null)
        ]);

        if (projRes && projRes.ok) setProjects(await projRes.json());
        if (jobsRes && jobsRes.ok) setJobs(await jobsRes.json());
      } catch (err) {
        console.error(err);
      }
    };
    fetchData();
  }, []);

  const successfulJobs = jobs.filter(j => j.status === 'SUCCESS');
  const latestJob = jobs[0];

  const getStepStatus = (stepIndex: number, currentJob: JobSummary | undefined) => {
    if (!currentJob) return 'PENDING';
    if (currentJob.status === 'FAILED' || currentJob.status === 'CANCELLED') {
       const currentStageIndex = PIPELINE_STEPS.findIndex(s => s.stageNames.includes(currentJob.current_stage || ''));
       if (currentStageIndex === -1) return currentJob.status;
       if (stepIndex < currentStageIndex) return 'COMPLETED';
       if (stepIndex === currentStageIndex) return currentJob.status;
       return 'UNAVAILABLE';
    }
    if (currentJob.status === 'SUCCESS') return 'COMPLETED';
    
    const currentStageIndex = PIPELINE_STEPS.findIndex(s => s.stageNames.includes(currentJob.current_stage || ''));
    if (currentStageIndex === -1) {
       if (currentJob.status === 'UPLOADED') return stepIndex === 0 ? 'COMPLETED' : 'PENDING';
       return 'PENDING';
    }
    if (stepIndex < currentStageIndex) return 'COMPLETED';
    if (stepIndex === currentStageIndex) return 'RUNNING';
    return 'PENDING';
  };

  const projectImages = [ucInfrastructureImg, ucDisasterImg, ucUrbanImg, ucRoadImg];

  const useCases = [
    { img: ucInfrastructureImg, icon: <Building2 className="w-4 h-4"/>, title: 'Infrastructure Inspection', desc: 'Bridge & structural health mapping' },
    { img: ucDisasterImg, icon: <ShieldAlert className="w-4 h-4"/>, title: 'Disaster Assessment', desc: 'Flood & damage rapid evaluation' },
    { img: ucUrbanImg, icon: <Map className="w-4 h-4"/>, title: 'Urban Mapping', desc: 'High-density terrain digitization' },
    { img: ucRoadImg, icon: <Waypoints className="w-4 h-4"/>, title: 'Road & Highway Survey', desc: 'Linear infrastructure reconstruction' },
    { img: ucEmergencyImg, icon: <Zap className="w-4 h-4"/>, title: 'Emergency Reconnaissance', desc: 'Rapid 3D situational awareness' }
  ];

  return (
    <div className="w-full relative pb-8 max-w-[1440px] mx-auto space-y-6">
      
      {/* 1. PAGE HEADER */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 pb-2">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-100 tracking-tight">Geospatial Operations Center</h1>
          <p className="text-slate-400 text-sm mt-1 tracking-wide">AERO RECON-3D Field Deployment Dashboard</p>
        </div>
        <Link 
          to="/reconstruction/new"
          className="w-full md:w-auto bg-blue-600 hover:bg-blue-500 text-white px-5 py-2.5 rounded-lg font-medium flex items-center justify-center gap-2 transition-all shadow-[0_0_15px_rgba(37,99,235,0.3)] hover:shadow-[0_0_20px_rgba(37,99,235,0.5)]"
        >
          <Plus className="w-5 h-5" />
          New Reconstruction
        </Link>
      </div>

      {/* 2. HERO / MISSION VISUAL */}
      <div className="bg-navy-900 border border-navy-700/60 rounded-2xl overflow-hidden shadow-2xl relative min-h-[280px] md:min-h-[340px] flex items-center group w-full">
        <img 
          src={heroSurveyImg} 
          alt="UAV Aerial Survey" 
          className="absolute right-0 top-0 w-2/3 h-full object-cover opacity-80" 
          loading="lazy" 
        />
        
        {/* Gradient overlays to blend the image into the dark left side */}
        <div className="absolute inset-0 bg-gradient-to-r from-navy-950 via-navy-950/90 to-transparent w-full md:w-3/4" />
        <div className="absolute inset-0 bg-gradient-to-t from-navy-950 via-transparent to-transparent opacity-80" />
        
        {settings.showDemoBadges && (
          <div className="absolute top-6 right-6 hidden md:flex flex-col items-end gap-1 font-mono text-[9px] text-cyan-400 bg-navy-900/60 border border-cyan-500/20 px-3 py-1.5 rounded backdrop-blur-md">
            <span>COORD: {latestJob?.has_telemetry ? "AVAILABLE" : "UNAVAILABLE"}</span>
            <span className="text-slate-400">ALT: {latestJob?.has_telemetry ? "LOGGED" : "UNAVAILABLE"}</span>
            <span className="text-[7px] text-slate-500 uppercase tracking-widest mt-0.5">VISUAL SAMPLE</span>
          </div>
        )}

        <div className="relative z-10 p-8 md:p-12 md:w-2/3">
          <h1 className="text-3xl md:text-5xl font-bold text-slate-100 tracking-tight leading-[1.15] mb-4">
            Transform Drone Footage <br />
            into <span className="text-cyan-400">Real-World Impact</span>
          </h1>
          <p className="text-slate-300 md:text-lg max-w-lg opacity-90 font-light tracking-wide">
            Capture. Process. Visualize. Analyze.
          </p>
        </div>
        
        <div className="absolute bottom-8 left-8 md:left-12">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse shadow-[0_0_8px_rgba(239,68,68,1)]" />
            <span className="text-[10px] font-bold tracking-widest text-slate-200 uppercase">Live Reconnaissance</span>
          </div>
        </div>
      </div>

      {/* 3 & 4. PROCESSING PIPELINE & TELEMETRY */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 w-full">
        {/* PROCESSING PIPELINE */}
        <div className="xl:col-span-2 bg-navy-900/80 border border-navy-700/80 rounded-xl p-5 shadow-lg relative overflow-hidden">
          <div className="flex justify-between items-start mb-6">
            <h2 className="text-sm font-semibold text-slate-100 tracking-wide uppercase">Processing Pipeline — Latest Job</h2>
            <div className="text-[10px] text-slate-500 font-mono">
              {latestJob ? latestJob.job_id.substring(0, 6).toUpperCase() : 'NONE'}
            </div>
          </div>
          
          <div className="flex items-center justify-between w-full relative z-10 px-2 overflow-x-auto hide-scrollbar pb-2">
            {/* Connecting line */}
            <div className="absolute top-[14px] left-8 right-8 h-[2px] bg-navy-700 -z-10" />
            
            {PIPELINE_STEPS.map((step, i) => {
              const status = getStepStatus(i, latestJob);
              const isCompleted = status === 'COMPLETED';
              const isRunning = status === 'RUNNING';
              const isFailed = status === 'FAILED';
              const isCancelled = status === 'CANCELLED';
              
              return (
                <div key={step.label} className="flex flex-col items-center gap-3 relative min-w-[70px]">
                  {/* Circle Indicator */}
                  <div className={cn(
                    "w-7 h-7 rounded-full flex items-center justify-center border-2 bg-navy-900 transition-all",
                    isCompleted ? "border-green-500 text-green-400 shadow-[0_0_10px_rgba(34,197,94,0.3)]" :
                    isRunning ? "border-blue-500 text-blue-400 shadow-[0_0_10px_rgba(59,130,246,0.5)] animate-pulse" :
                    isFailed ? "border-red-500 text-red-400 shadow-[0_0_10px_rgba(239,68,68,0.3)]" :
                    isCancelled ? "border-slate-500 text-slate-400 shadow-[0_0_10px_rgba(100,116,139,0.3)]" :
                    "border-navy-600 text-slate-600"
                  )}>
                    {isCompleted ? <CheckCircle2 className="w-4 h-4" /> : 
                     isFailed ? <XCircle className="w-4 h-4" /> :
                     isCancelled ? <XCircle className="w-4 h-4" /> :
                     isRunning ? <div className="w-2 h-2 rounded-full bg-blue-400 animate-ping" /> :
                     <div className="w-1.5 h-1.5 rounded-full bg-slate-600" />}
                  </div>
                  
                  {/* Label */}
                  <span className={cn(
                    "text-[9px] font-medium tracking-wide text-center uppercase leading-tight",
                    isCompleted ? "text-slate-300" :
                    isRunning ? "text-blue-400 font-bold" :
                    isFailed ? "text-red-400" :
                    isCancelled ? "text-slate-400" :
                    "text-slate-500"
                  )}>
                    {step.label}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* TELEMETRY STATUS */}
        <div className="bg-navy-900/80 border border-navy-700/80 rounded-xl p-5 shadow-lg flex flex-col justify-center relative overflow-hidden">
          <h2 className="text-sm font-semibold text-slate-100 mb-6 tracking-wide uppercase flex items-center gap-2">
            <Navigation className="w-4 h-4 text-blue-400" />
            Telemetry Status
          </h2>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-navy-700/50">
              <span className="text-sm text-slate-400">GPS / IMU</span>
              {latestJob && latestJob.has_telemetry ? (
                 <span className="text-[10px] font-bold text-green-400 border border-green-500/50 bg-green-500/10 px-2.5 py-1 rounded-full uppercase tracking-wider">AVAILABLE</span>
              ) : (
                 <span className="text-[10px] font-bold text-amber-500 border border-amber-500/50 bg-amber-500/10 px-2.5 py-1 rounded-full uppercase tracking-wider">UNAVAILABLE</span>
              )}
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-400">Coordinates</span>
              {latestJob && latestJob.has_telemetry ? (
                 <span className="text-[10px] font-bold text-blue-400 border border-blue-500/50 bg-blue-500/10 px-2.5 py-1 rounded-full uppercase tracking-wider">GEOREFERENCED</span>
              ) : (
                 <span className="text-[10px] font-bold text-slate-400 border border-navy-600 bg-navy-800 px-2.5 py-1 rounded-full uppercase tracking-wider">LOCAL / RELATIVE</span>
              )}
            </div>
          </div>
        </div>
      </div>      {/* 2. MY PROJECTS */}
      <div className="mb-8">
        <div className="flex justify-between items-end mb-4">
          <h2 className="text-xl font-bold text-slate-100 tracking-tight">My Projects</h2>
          <Link to="/projects" className="text-blue-400 text-xs font-medium hover:text-blue-300 transition-colors uppercase tracking-wider flex items-center gap-1">
            View All <span className="text-lg leading-none">→</span>
          </Link>
        </div>
        
        {projects.length > 0 ? (
          <div className="flex gap-4 overflow-x-auto pb-4 snap-x hide-scrollbar -mx-4 px-4 sm:mx-0 sm:px-0">
            {projects.slice(0, 5).map((project, idx) => (
              <div 
                key={project.id} 
                className="flex-none w-[280px] bg-navy-900/80 border border-navy-700/80 rounded-xl overflow-hidden hover:border-blue-500/50 transition-colors group cursor-pointer snap-start shadow-xl relative"
                onClick={() => navigate(`/projects/${project.id}`)}
              >
                <div className="h-32 w-full bg-navy-800 border-b border-navy-700/50 relative overflow-hidden">
                  <img 
                    src={projectImages[idx % projectImages.length]} 
                    alt="Project visual" 
                    className="w-full h-full object-cover opacity-80 group-hover:opacity-100 group-hover:scale-105 transition-all duration-700" 
                    loading="lazy"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-navy-900 via-transparent to-transparent opacity-80" />
                </div>
                <div className="p-4 relative">
                  <div className="absolute right-4 top-4">
                    <MoreVertical className="w-4 h-4 text-slate-500 hover:text-slate-300" />
                  </div>
                  <h3 className="font-semibold text-slate-100 mb-2 truncate pr-6">{project.name}</h3>
                  <div className="flex flex-col gap-2">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded text-[9px] font-bold tracking-wider uppercase bg-green-500/20 text-green-400 border border-green-500/30">
                        COMPLETED
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 mt-1">
                      {formatDate(project.created_at)}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-navy-900/50 border border-navy-700/50 border-dashed rounded-xl p-8 text-center">
            <FolderKanban className="w-8 h-8 text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400 text-sm">No projects created yet.</p>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 mb-8">
        {/* 3. RECENT FLIGHTS / VIDEOS */}
        <div>
          <div className="flex justify-between items-end mb-4">
            <h2 className="text-xl font-bold text-slate-100 tracking-tight">Recent Flights / Videos</h2>
            <Link to="/reconstruction/new" className="text-blue-400 text-xs font-medium hover:text-blue-300 transition-colors uppercase tracking-wider flex items-center gap-1">
              View All <span className="text-lg leading-none">→</span>
            </Link>
          </div>
          
          <div className="flex flex-col gap-3">
            {jobs.length > 0 ? (
              jobs.slice(0, 4).map((job, idx) => {
                const statusColor = 
                  job.status === 'SUCCESS' ? 'bg-green-500/20 text-green-400 border-green-500/30' :
                  job.status === 'FAILED' ? 'bg-red-500/20 text-red-400 border-red-500/30' :
                  (job.status === 'RUNNING' || job.status === 'QUEUED') ? 'bg-blue-500/20 text-blue-400 border-blue-500/30' : 
                  'bg-navy-700 text-slate-400 border-navy-600';
                
                return (
                  <div key={job.job_id} className="bg-navy-900/80 border border-navy-700/80 rounded-xl p-3 flex items-center gap-4 hover:border-navy-500 transition-colors cursor-pointer group shadow-md" onClick={() => navigate('/processing', { state: { jobId: job.job_id } })}>
                    <div className="w-[120px] h-[70px] bg-navy-800 rounded-lg relative overflow-hidden flex-shrink-0">
                      <img 
                        src={projectImages[idx % projectImages.length]} 
                        alt="Video thumbnail" 
                        className="w-full h-full object-cover opacity-70 group-hover:opacity-100 transition-opacity" 
                        loading="lazy"
                      />
                    </div>
                    <div className="flex-1 min-w-0 flex flex-col justify-between h-[70px] py-0.5">
                      <div>
                        <div className="flex justify-between items-start">
                          <h3 className="font-semibold text-slate-200 text-sm truncate mb-1 pr-2">{job.video_filename}</h3>
                          <MoreVertical className="w-4 h-4 text-slate-600 hover:text-slate-400 flex-shrink-0" />
                        </div>
                        <div className="text-[10px] text-slate-400">
                          {formatDate(job.created_at)}
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className={cn("px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider border", statusColor)}>
                          {getStatusLabel(job.status)}
                        </span>
                        <div className="flex items-center gap-1.5 text-[9px] text-slate-400">
                          <Navigation className={cn("w-3 h-3", job.has_telemetry ? "text-cyan-400" : "text-slate-600")} />
                          Telemetry: <span className={job.has_telemetry ? "text-cyan-400" : "text-amber-500/80"}>{job.has_telemetry ? 'Available' : 'Unavailable'}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="bg-navy-900/50 border border-navy-700/50 border-dashed rounded-xl p-8 text-center">
                <Video className="w-8 h-8 text-slate-600 mx-auto mb-3" />
                <p className="text-slate-400 text-sm">No recent flights found.</p>
              </div>
            )}
          </div>
        </div>

        {/* 4. RECENT 3D MODELS */}
        <div>
          <div className="flex justify-between items-end mb-4">
            <h2 className="text-xl font-bold text-slate-100 tracking-tight">Recent 3D Models</h2>
            <Link to="/projects" className="text-blue-400 text-xs font-medium hover:text-blue-300 transition-colors uppercase tracking-wider flex items-center gap-1">
              View All <span className="text-lg leading-none">→</span>
            </Link>
          </div>
          
          <div className="flex flex-col gap-3">
            {successfulJobs.length > 0 ? (
              successfulJobs.slice(0, 4).map((job, idx) => (
                <div key={job.job_id} className="bg-navy-900/80 border border-navy-700/80 rounded-xl p-3 flex items-center gap-4 hover:border-navy-500 transition-colors cursor-pointer shadow-md" onClick={() => navigate(`/?jobId=${job.job_id}`)}>
                  <div className="w-[120px] h-[70px] bg-navy-800 rounded-lg relative overflow-hidden flex-shrink-0 flex items-center justify-center border border-navy-700/50">
                     {/* Pseudo wireframe background */}
                    <div className="absolute inset-0 bg-[linear-gradient(to_right,#0ea5e910_1px,transparent_1px),linear-gradient(to_bottom,#0ea5e910_1px,transparent_1px)] bg-[size:10px_10px]" />
                    <img 
                      src={projectImages[idx % projectImages.length]} 
                      alt="Model visual" 
                      className="w-[80%] h-[80%] object-cover opacity-60 mix-blend-screen mask-image-gradient" 
                      loading="lazy"
                    />
                  </div>
                  <div className="flex-1 min-w-0 flex flex-col justify-between h-[70px] py-0.5">
                    <div>
                      <h3 className="font-semibold text-slate-200 text-sm truncate mb-1">Model_{job.job_id.substring(0,8)}.glb</h3>
                      <div className="text-[10px] text-slate-400 font-mono">
                        {job.point_count ? `${(job.point_count / 1000000).toFixed(1)}M pts` : '— pts'}
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        {job.has_glb && <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-navy-800 border border-navy-600 text-slate-300">GLB ✓</span>}
                        {job.has_ply && <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-navy-800 border border-navy-600 text-slate-300">PLY ✓</span>}
                      </div>
                      {job.has_telemetry ? (
                         <span className="px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider bg-green-900/40 text-green-400 border border-green-500/30 flex items-center gap-1">
                           <Map className="w-2.5 h-2.5" /> GEOREFERENCED
                         </span>
                      ) : (
                         <span className="px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider bg-navy-800 text-slate-400 border border-navy-600">
                           LOCAL / RELATIVE
                         </span>
                      )}
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="bg-navy-900/50 border border-navy-700/50 border-dashed rounded-xl p-8 text-center">
                <Box className="w-8 h-8 text-slate-600 mx-auto mb-3" />
                <p className="text-slate-400 text-sm">No 3D models available yet.</p>
              </div>
            )}
          </div>
        </div>
      </div>
      {/* 8. OPERATIONAL USE CASES */}
      <div className="w-full pt-4 pb-4">
        <h2 className="text-lg font-bold text-slate-100 mb-4 px-1 tracking-wide">Operational Use Cases</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {useCases.map((uc, i) => (
            <div key={i} className="bg-[#0A1224] border border-navy-700/50 rounded-xl overflow-hidden hover:border-cyan-500/40 transition-all duration-300 group flex flex-col shadow-sm">
              <div className="h-24 w-full relative overflow-hidden bg-[#050A15] border-b border-navy-700/50">
                <img 
                  src={uc.img} 
                  alt={uc.title} 
                  className="w-full h-full object-cover opacity-60 group-hover:opacity-90 group-hover:scale-105 transition-all duration-700" 
                  loading="lazy" 
                />
                <div className="absolute inset-0 bg-gradient-to-t from-[#0A1224] to-transparent" />
              </div>
              <div className="p-4 pt-1 flex-1 flex flex-col">
                <div className="bg-navy-900 border border-navy-700 w-8 h-8 rounded flex items-center justify-center text-cyan-400 -mt-4 relative z-10 shadow-sm mb-3 group-hover:bg-cyan-900/40 transition-colors">
                  {uc.icon}
                </div>
                <h3 className="text-sm font-semibold text-slate-200 mb-1.5 leading-snug">{uc.title}</h3>
                <p className="text-[11px] text-slate-400 leading-snug font-light">{uc.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 9. FOOTER / SYSTEM STATUS */}
      <div className="mt-8 pt-6 border-t border-navy-700/50 flex flex-col md:flex-row items-center justify-between gap-4 text-xs">
        <div className="flex flex-col md:flex-row items-center gap-4 text-slate-400">
          <div className="font-semibold text-slate-300 tracking-wide">AERO RECON-3D <span className="font-light">| Field Deployment System</span></div>
          <div className="hidden md:block w-1 h-1 rounded-full bg-slate-600" />
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
              <span>Backend: Connected</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
              <span>Processing Engine: Ready</span>
            </div>
          </div>
        </div>
        <div className="text-slate-500 font-mono tracking-wider">
          V.1.0.0-RC1
        </div>
      </div>

    </div>
  );
}
