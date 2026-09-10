import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Check, Loader2, Film, Sparkles, Camera, Layers, Box, AlertTriangle, XCircle
} from 'lucide-react';
import { apiFetch } from '../utils/api';
import { safeSetStorage, safeGetStorage } from '../utils/storage';

interface JobStatus {
  job_id: string;
  status: string; // QUEUED | RUNNING | SUCCESS | FAILED | UPLOADED
  progress: string;
  current_stage?: string;
  stage_progress?: number;
  telemetry_path?: string;
  point_count?: number;
  elapsed_seconds?: number;
  error?: string;
}

interface PipelineStageDef {
  name: string;
  backendStage: string | null;
  statusType: 'implemented' | 'partial' | 'unavailable' | 'not_implemented';
  subtitle?: string;
  unavailableLabel?: string;
}

const PIPELINE_STAGES: PipelineStageDef[] = [
  { name: 'Data Acquisition', backendStage: 'UPLOADED', statusType: 'implemented' },
  { name: 'Frame Extraction', backendStage: 'Frame Extraction', statusType: 'implemented' },
  { name: 'Feature Tracking', backendStage: 'Feature Tracking', statusType: 'implemented' },
  { name: 'Camera Pose Estimation', backendStage: 'Pose Estimation', statusType: 'implemented' },
  { name: 'Depth Estimation', backendStage: 'Depth Estimation', statusType: 'implemented' },
  { 
    name: 'GPS / IMU Telemetry', 
    backendStage: null, 
    statusType: 'unavailable',
    subtitle: 'Source video contains no GPS/IMU telemetry',
    unavailableLabel: 'Metadata Unavailable'
  },
  { 
    name: 'GPS / IMU Spatial Fusion', 
    backendStage: null, 
    statusType: 'unavailable',
    unavailableLabel: 'Unavailable — No GPS/IMU Data'
  },
  { name: 'Point Cloud Generation', backendStage: 'Point Cloud', statusType: 'implemented' },
  { 
    name: '3D Reconstruction', 
    backendStage: 'Mesh Generation', 
    statusType: 'implemented',
    subtitle: 'Point cloud available'
  },
  {
    name: 'Metric / Georeferenced Point Cloud',
    backendStage: null,
    statusType: 'unavailable',
    unavailableLabel: 'Unavailable — No Metric Reference'
  },
  { 
    name: 'Reprojection Validation', 
    backendStage: null, 
    statusType: 'implemented',
    subtitle: 'Image-space validation available'
  },
  { 
    name: 'Metric Accuracy', 
    backendStage: null, 
    statusType: 'unavailable',
    unavailableLabel: 'Unavailable — No Ground Truth'
  },
  { name: 'Mesh Generation', backendStage: 'Mesh Generation', statusType: 'implemented' },
  { name: 'Vertex-Colored GLB Export', backendStage: 'Vertex-Colored GLB', statusType: 'implemented' }
];

const backendStageOrder = [
  'UPLOADED',
  'Initializing',
  'Frame Extraction',
  'Feature Tracking',
  'Pose Estimation',
  'Depth Estimation',
  'Point Cloud',
  'Mesh Generation',
  'Vertex-Colored GLB',
  'Finalizing',
  'Complete',
  'Failed'
];

export default function Processing() {
  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);
  const jobId = location.state?.jobId || searchParams.get('jobId') || safeGetStorage('last_job_id');

  const [jobState, setJobState] = useState<JobStatus | null>(null);
  const [report, setReport] = useState<any>(null);
  const [networkError, setNetworkError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    let timer: ReturnType<typeof setTimeout>;
    const abortController = new AbortController();

    if (jobId) {
       safeSetStorage('last_job_id', jobId);
    } else {
       setNetworkError("Reconstruction job unavailable. No job specified.");
       return;
    }

    const pollStatus = async () => {
      if (!isMounted) return;
      try {
        const res = await apiFetch(`/status/${jobId}`, {
          signal: abortController.signal
        });
        if (!res.ok) {
          if (res.status === 404) {
            setNetworkError("Reconstruction job no longer available.");
            return;
          }
          throw new Error('Status fetch failed');
        }
        
        const data = await res.json();
        
        // Prevent state update if unmounted
        if (!isMounted) return;
        
        setJobState(data);
        
        if (data.status === 'SUCCESS' || data.status === 'FAILED') {
          // Set active job for Viewer and fetch report path
          safeSetStorage('last_job_id', jobId);
          try {
            const reportRes = await apiFetch(`/report/${jobId}`, { signal: abortController.signal });
            if (reportRes.ok) {
              const reportData = await reportRes.json();
              if (isMounted) setReport(reportData);
            }
          } catch (e) {
            // ignore fetch errors
          }
        }

        if (data.status !== 'SUCCESS' && data.status !== 'FAILED' && data.status !== 'CANCELLED') {
          timer = setTimeout(pollStatus, 2000);
        }
      } catch (err: any) {
        if (!isMounted || err.name === 'AbortError') return;
        setNetworkError("Backend unavailable. Please check your connection.");
        timer = setTimeout(pollStatus, 5000);
      }
    };

    pollStatus();

    return () => {
      isMounted = false;
      clearTimeout(timer);
      abortController.abort();
    };
  }, [jobId]);

  const [isCancelling, setIsCancelling] = useState(false);

  const cancelProcessing = async () => {
    if (window.confirm('Cancel this reconstruction?')) {
      setIsCancelling(true);
      try {
        const res = await apiFetch(`/cancel/${jobId}`, { method: 'POST' });
        if (res.ok) {
           setJobState(prev => prev ? { ...prev, status: 'CANCELLED', progress: 'Cancelled by user', current_stage: 'Cancelled' } : null);
        } else {
           alert('Unable to cancel reconstruction. Please try again.');
        }
      } catch (err) {
        alert('Unable to cancel reconstruction. Please try again.');
      } finally {
        setIsCancelling(false);
      }
    }
  };

  const isCompleted = jobState?.status === 'SUCCESS';
  const isFailed = jobState?.status === 'FAILED';
  const isCancelled = jobState?.status === 'CANCELLED';
  const isUnavailable = !jobId || (networkError && networkError.includes("no longer available"));
  
  const currentBackendIndex = backendStageOrder.indexOf(jobState?.current_stage || 'UPLOADED');
  
  const overallProgress = isCompleted ? 100 : isFailed || isUnavailable ? 0 : (() => {
    const implementedStages = PIPELINE_STAGES.filter(s => s.statusType === 'implemented' || s.statusType === 'partial');
    
    let implIndex = -1;
    for (let j = currentBackendIndex; j >= 0; j--) {
      const stageName = backendStageOrder[j];
      const foundIdx = implementedStages.findIndex(s => s.backendStage === stageName);
      if (foundIdx > -1) {
        implIndex = foundIdx;
        break;
      }
    }
    
    if (implIndex === -1) return 0;
    
    const base = (implIndex / implementedStages.length) * 100;
    const isExactMatch = implementedStages[implIndex].backendStage === jobState?.current_stage;
    const currentProg = isExactMatch && jobState?.stage_progress ? (jobState.stage_progress / 100) : 0;
    const current = currentProg * (100 / implementedStages.length);
    return Math.min(99, Math.round(base + current));
  })();

  const formatTime = (secs: number) => {
    if (!secs) return '';
    const m = Math.floor(secs / 60);
    const s = Math.round(secs % 60);
    return `${m}m ${s}s`;
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6 pt-20 md:pt-4 pb-28 md:pb-8 px-4 md:px-0">
      <div>
        <div className="flex items-center gap-3 mb-1">
          <h1 className="text-xl md:text-2xl font-bold text-slate-100">
            {isUnavailable ? 'Reconstruction Job Unavailable' : isCompleted ? 'Model Generated Successfully' : isFailed ? 'Reconstruction Failed' : isCancelled ? 'Reconstruction Cancelled' : 'Reconstruction in Progress'}
          </h1>
          {(!isUnavailable && !isCompleted && !isFailed && !isCancelled) && (
            jobState?.status === 'RUNNING' || jobState?.status === 'QUEUED' ? (
              <span className="bg-blue-500/10 text-blue-400 text-xs px-2.5 py-1 rounded-full font-medium tracking-wide">LIVE</span>
            ) : jobState?.status === 'UPLOADED' ? (
              <span className="bg-slate-500/10 text-slate-400 text-xs px-2.5 py-1 rounded-full font-medium tracking-wide uppercase">READY / WAITING</span>
            ) : null
          )}
        </div>
        <p className="text-slate-400 font-mono text-sm">Job ID: {jobId || 'Unknown'}</p>
      </div>

      {networkError && (
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 flex items-center gap-3 text-amber-400 shadow-sm">
          <AlertTriangle className="w-5 h-5 shrink-0" />
          <p className="text-sm font-medium">{networkError}</p>
        </div>
      )}

      {isCancelled && (
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-4 flex items-center gap-3 text-slate-400 shadow-sm">
          <XCircle className="w-5 h-5 shrink-0" />
          <p className="text-sm font-medium">This reconstruction was cancelled by the user.</p>
        </div>
      )}

      {isFailed && jobState?.error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-5 flex flex-col gap-3 text-red-400 shadow-sm">
          <div className="flex items-center gap-3">
            <XCircle className="w-5 h-5 shrink-0" />
            <p className="font-bold tracking-wide uppercase text-xs">Pipeline Error</p>
          </div>
          <p className="text-sm font-mono bg-red-950/50 p-3 rounded-lg border border-red-900/30">{jobState.error}</p>
        </div>
      )}

      <div className="bg-[#0A1224] border border-navy-700/50 rounded-2xl p-6 md:p-8 shadow-sm relative overflow-hidden">
        {/* Subtle grid background */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#0ea5e905_1px,transparent_1px),linear-gradient(to_bottom,#0ea5e905_1px,transparent_1px)] bg-[size:20px_20px] pointer-events-none" />
        
        <div className="flex flex-col md:flex-row md:items-center gap-6 relative z-10">
          <div className={`text-5xl md:text-6xl font-bold tracking-tight bg-clip-text text-transparent shrink-0 ${isFailed || isUnavailable || isCancelled ? 'bg-gradient-to-r from-slate-400 to-slate-500' : 'bg-gradient-to-r from-cyan-400 to-blue-500'}`}>
            {isUnavailable ? '—' : `${overallProgress}%`}
          </div>
          <div className="flex-1">
            <p className="text-[11px] uppercase tracking-widest text-cyan-400 mb-3 font-bold">
              {isUnavailable ? '—' : (jobState?.progress || 'WAITING FOR BACKEND...')}
            </p>
            <div className="h-2 bg-[#050A15] rounded-full overflow-hidden border border-navy-700/50">
              <div 
                className={`h-full rounded-full transition-all duration-1000 shadow-[0_0_15px_rgba(34,211,238,0.5)] ${isFailed ? 'bg-red-500' : 'bg-gradient-to-r from-blue-500 to-cyan-400'}`} 
                style={{ width: `${overallProgress}%` }} 
              />
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-[#0A1224] border border-navy-700/50 rounded-2xl p-6 md:p-8 shadow-sm">
            <h2 className="text-xs font-bold text-cyan-500 uppercase tracking-widest mb-6">Processing Pipeline</h2>
            <div className="space-y-6 relative">
              <div className="absolute left-5 top-10 bottom-10 w-[1px] bg-navy-700" />
              
              {PIPELINE_STAGES.map((baseStageDef, i) => {
                let stageDef = { ...baseStageDef };

                const reportString = report ? JSON.stringify(report) : "";

                // Dynamic Telemetry State
                if (stageDef.name === 'GPS / IMU Telemetry') {
                  if (reportString.includes('GPS_AVAILABLE') || reportString.includes('TELEMETRY_SYNC_AVAILABLE')) {
                    stageDef.statusType = 'implemented';
                    stageDef.subtitle = 'GPS/IMU synchronized';
                  } else if (!isCompleted && jobState?.telemetry_path) {
                    stageDef.statusType = 'partial';
                    stageDef.subtitle = 'Telemetry file supplied...';
                  } else {
                    stageDef.statusType = 'unavailable';
                    stageDef.unavailableLabel = 'GPS/IMU UNAVAILABLE';
                  }
                }
                
                if (stageDef.name === 'GPS / IMU Spatial Fusion' || stageDef.name === 'Metric / Georeferenced Point Cloud') {
                  if (reportString.includes('METRIC_ALIGNMENT_AVAILABLE') || reportString.includes('GPS_ENU_AVAILABLE') || reportString.includes('CAMERA_GPS_CORRESPONDENCE_AVAILABLE')) {
                    stageDef.statusType = 'implemented';
                    stageDef.subtitle = 'Metric alignment applied';
                  } else if (!isCompleted && jobState?.telemetry_path) {
                    stageDef.statusType = 'partial';
                    stageDef.subtitle = 'Awaiting metric alignment...';
                  } else {
                    stageDef.statusType = 'unavailable';
                    stageDef.unavailableLabel = 'Metric alignment unavailable';
                  }
                }
                
                if (stageDef.name === 'Metric Accuracy') {
                  if (reportString.includes('METRIC_ACCURACY_AVAILABLE')) {
                    stageDef.statusType = 'implemented';
                    stageDef.subtitle = 'Metric accuracy evaluated';
                  } else {
                    stageDef.statusType = 'unavailable';
                    stageDef.unavailableLabel = 'Metric accuracy unavailable';
                  }
                }

                let status: 'pending' | 'processing' | 'completed' | 'not_implemented' | 'unavailable' | 'partial' | 'failed' | 'not_run' = 'pending';
                
                if (stageDef.name === '3D Reconstruction') {
                  const pcStageIndex = backendStageOrder.indexOf('Point Cloud');
                  if (currentBackendIndex > pcStageIndex || isCompleted) {
                      stageDef.subtitle = 'Point cloud available';
                  } else {
                      stageDef.subtitle = undefined;
                  }
                }

                if (isUnavailable) {
                  status = 'not_run';
                  stageDef.subtitle = undefined;
                } else if (stageDef.statusType === 'not_implemented') {
                  status = 'not_implemented';
                } else if (stageDef.statusType === 'unavailable') {
                  status = 'unavailable';
                } else if (stageDef.statusType === 'partial') {
                  status = 'partial';
                } else {
                  if (isCompleted) {
                    status = 'completed';
                  } else if (currentBackendIndex > -1 && stageDef.backendStage) {
                    const thisStageIndex = backendStageOrder.indexOf(stageDef.backendStage);
                    if (thisStageIndex > -1) {
                      if (currentBackendIndex > thisStageIndex) {
                        status = 'completed';
                      } else if (currentBackendIndex === thisStageIndex) {
                        status = isFailed ? 'failed' : 'processing';
                      } else {
                        status = isFailed ? 'not_run' : 'pending';
                      }
                    } else if (!stageDef.backendStage) {
                       status = 'completed'; 
                    }
                  }
                  
                  if (stageDef.backendStage === 'UPLOADED' && status !== 'failed') {
                    status = 'completed';
                  }
                }
                
                if ((stageDef.name === 'GPS / IMU Telemetry' || stageDef.name === 'GPS / IMU Spatial Fusion' || stageDef.name === 'Metric / Georeferenced Point Cloud') && stageDef.statusType === 'implemented') {
                    if (currentBackendIndex >= backendStageOrder.indexOf('Point Cloud')) {
                        status = 'completed';
                    } else if (currentBackendIndex >= backendStageOrder.indexOf('Feature Tracking')) {
                        status = 'processing';
                    } else {
                        status = 'pending';
                    }
                }

                return (
                  <div key={stageDef.name} className={`flex items-center gap-3 relative z-10 ${status === 'not_implemented' ? 'opacity-40' : ''}`}>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 border transition-all duration-300 ${
                      status === 'completed' ? 'bg-[#050A15] border-green-500/50 text-green-400 shadow-[0_0_15px_rgba(34,197,94,0.2)]' :
                      status === 'processing' ? 'bg-[#050A15] border-cyan-500 text-cyan-400 shadow-[0_0_15px_rgba(34,211,238,0.4)]' :
                      status === 'not_implemented' ? 'bg-[#050A15] border-red-500/30 text-red-400' :
                      status === 'unavailable' ? 'bg-[#050A15] border-amber-500/30 text-amber-500' :
                      status === 'partial' ? 'bg-[#050A15] border-purple-500/40 text-purple-400' :
                      status === 'failed' ? 'bg-[#050A15] border-red-500/60 text-red-500 shadow-[0_0_15px_rgba(239,68,68,0.4)]' :
                      'bg-[#050A15] border-navy-700 text-slate-500'
                    }`}>
                      {status === 'completed' ? <Check size={14} /> :
                       status === 'processing' ? <Loader2 size={14} className="animate-spin" /> :
                       status === 'not_implemented' ? <XCircle size={14} /> :
                       status === 'unavailable' ? <AlertTriangle size={14} /> :
                       status === 'partial' ? <Box size={14} /> :
                       status === 'failed' ? <XCircle size={14} /> :
                       <span className="text-[9px] font-bold">{i + 1}</span>}
                    </div>
                    <div className={`flex-1 rounded-lg p-3 border shadow-sm ${status === 'not_implemented' ? 'bg-[#050A15]/50 border-red-900/30' : status === 'unavailable' ? 'bg-[#050A15] border-amber-900/30' : status === 'failed' ? 'bg-red-950/20 border-red-500/30' : 'bg-[#050A15] border-navy-700'}`}>
                      <div className="flex justify-between items-center gap-2">
                        <div className="flex flex-col justify-center">
                          <h3 className={`font-semibold text-xs tracking-wide leading-tight ${status === 'not_implemented' ? 'text-slate-500 line-through' : status === 'unavailable' || status === 'not_run' ? 'text-slate-400' : 'text-slate-200'}`}>
                            {stageDef.name}
                          </h3>
                          {stageDef.subtitle && (
                            <p className={`text-[9px] uppercase tracking-widest mt-0.5 font-medium leading-tight ${status === 'unavailable' || status === 'not_run' ? 'text-amber-500/80' : status === 'partial' ? 'text-purple-400/80' : 'text-cyan-400/80'}`}>
                              {stageDef.subtitle}
                            </p>
                          )}
                        </div>
                        <span className={`text-[8px] px-2 py-0.5 rounded uppercase tracking-widest font-bold border shrink-0 ${
                          status === 'completed' ? 'bg-green-500/10 text-green-400 border-green-500/20' :
                          status === 'processing' ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20' :
                          status === 'not_implemented' ? 'bg-red-500/5 text-red-500/50 border-red-500/10' :
                          status === 'unavailable' ? 'bg-amber-500/10 text-amber-500 border-amber-500/20' :
                          status === 'partial' ? 'bg-purple-500/10 text-purple-400 border-purple-500/20' :
                          status === 'failed' ? 'bg-red-500/10 text-red-500 border-red-500/20' :
                          'bg-navy-800/50 text-slate-500 border-navy-700'
                        }`}>
                          {status === 'not_implemented' ? 'Not Implemented' : 
                           status === 'not_run' ? 'Not Run' :
                           status === 'unavailable' ? (stageDef.unavailableLabel || 'Metadata Unavailable') : 
                           (status === 'completed' && stageDef.name === 'GPS / IMU Telemetry' ? 'GPS AVAILABLE' : 
                           status === 'partial' ? 'Partial' : 
                           status === 'failed' ? 'Failed' :
                           status)}
                        </span>
                      </div>
                      {status === 'processing' && jobState?.stage_progress !== undefined && (
                        <div className="mt-2.5 h-1 bg-[#050A15] rounded-full overflow-hidden border border-navy-700/50 w-full">
                          <div className="h-full bg-cyan-400 rounded-full transition-all duration-500 shadow-[0_0_10px_rgba(34,211,238,0.5)]" style={{ width: `${jobState.stage_progress}%` }} />
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-4">
            <div className={`bg-[#0A1224] border border-navy-700/50 rounded-xl p-4 relative group shadow-sm ${report ? '' : 'opacity-50'}`}>
              <div className="bg-blue-500/10 border border-blue-500/20 w-8 h-8 rounded-lg flex items-center justify-center mb-2">
                <Film className="w-4 h-4 text-blue-400" />
              </div>
              <div className="text-xl font-bold text-slate-100 font-mono tracking-tight">
                {report?.stages?.find((s:any)=>s.stage==='stage1_extraction')?.metrics?.frames_accepted || '--'}
              </div>
              <div className="text-[10px] uppercase tracking-widest text-slate-400 mt-1 font-bold">Frames Processed</div>
              {!report && <div className="absolute inset-0 bg-[#0A1224]/90 backdrop-blur-sm hidden group-hover:flex items-center justify-center rounded-xl text-[10px] font-bold text-slate-300 uppercase tracking-widest text-center px-2">Data not emitted</div>}
            </div>
            <div className={`bg-[#0A1224] border border-navy-700/50 rounded-xl p-4 relative group shadow-sm ${report ? '' : 'opacity-50'}`}>
              <div className="bg-purple-500/10 border border-purple-500/20 w-8 h-8 rounded-lg flex items-center justify-center mb-2">
                <Sparkles className="w-4 h-4 text-purple-400" />
              </div>
              <div className="text-xl font-bold text-slate-100 font-mono tracking-tight">
                {report?.stages?.find((s:any)=>s.stage==='stage2_features')?.metrics?.total_keypoints_detected 
                 ? new Intl.NumberFormat().format(report.stages.find((s:any)=>s.stage==='stage2_features').metrics.total_keypoints_detected) 
                 : '--'}
              </div>
              <div className="text-[10px] uppercase tracking-widest text-slate-400 mt-1 font-bold">Feature Points</div>
              {!report && <div className="absolute inset-0 bg-[#0A1224]/90 backdrop-blur-sm hidden group-hover:flex items-center justify-center rounded-xl text-[10px] font-bold text-slate-300 uppercase tracking-widest text-center px-2">Data not emitted</div>}
            </div>
            <div className={`bg-[#0A1224] border border-navy-700/50 rounded-xl p-4 relative group shadow-sm ${report ? '' : 'opacity-50'}`}>
              <div className="bg-green-500/10 border border-green-500/20 w-8 h-8 rounded-lg flex items-center justify-center mb-2">
                <Camera className="w-4 h-4 text-green-400" />
              </div>
              <div className="text-xl font-bold text-slate-100 font-mono tracking-tight">
                {report?.stages?.find((s:any)=>s.stage==='stage3_pose')?.metrics?.poses_accepted || '--'}
              </div>
              <div className="text-[10px] uppercase tracking-widest text-slate-400 mt-1 font-bold">Camera Poses</div>
              {!report && <div className="absolute inset-0 bg-[#0A1224]/90 backdrop-blur-sm hidden group-hover:flex items-center justify-center rounded-xl text-[10px] font-bold text-slate-300 uppercase tracking-widest text-center px-2">Data not emitted</div>}
            </div>
            <div className={`bg-[#0A1224] border border-navy-700/50 rounded-xl p-4 relative group shadow-sm ${report ? '' : 'opacity-50'}`}>
              <div className="bg-amber-500/10 border border-amber-500/20 w-8 h-8 rounded-lg flex items-center justify-center mb-2">
                <Layers className="w-4 h-4 text-amber-400" />
              </div>
              <div className="text-xl font-bold text-slate-100 font-mono tracking-tight">
                {report?.stages?.find((s:any)=>s.stage==='stage4_depth')?.metrics?.frames_depth_estimated || '--'}
              </div>
              <div className="text-[10px] uppercase tracking-widest text-slate-400 mt-1 font-bold">Depth Maps</div>
              {!report && <div className="absolute inset-0 bg-[#0A1224]/90 backdrop-blur-sm hidden group-hover:flex items-center justify-center rounded-xl text-[10px] font-bold text-slate-300 uppercase tracking-widest text-center px-2">Data not emitted</div>}
            </div>
            <div className="bg-[#0A1224] border border-navy-700/50 rounded-xl p-4 shadow-sm">
              <div className="bg-cyan-500/10 border border-cyan-500/20 w-8 h-8 rounded-lg flex items-center justify-center mb-2">
                <Box className="w-4 h-4 text-cyan-400" />
              </div>
              <div className="text-xl font-bold text-slate-100 font-mono tracking-tight">
                {jobState?.point_count ? new Intl.NumberFormat().format(jobState.point_count) : '--'}
              </div>
              <div className="text-[10px] uppercase tracking-widest text-cyan-500 mt-1 font-bold">Point Cloud</div>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-[#0A1224] border border-navy-700/50 rounded-2xl p-6 shadow-sm">
            <h2 className="text-xs font-bold text-cyan-500 uppercase tracking-widest mb-4">Duration</h2>
            <div className="text-3xl font-bold text-slate-200 font-mono tracking-tight">
              {isUnavailable ? '—' : jobState?.elapsed_seconds ? formatTime(jobState.elapsed_seconds) : (isCompleted ? 'Finished' : (isFailed ? '—' : 'Running...'))}
            </div>
            {isCompleted && <p className="text-[10px] font-bold tracking-widest uppercase text-green-400 mt-3">Pipeline completed successfully.</p>}
          </div>

          <div className="bg-[#0A1224] border border-navy-700/50 rounded-2xl p-6 shadow-sm">
            <h2 className="text-xs font-bold text-cyan-500 uppercase tracking-widest mb-4">Reconstruction Preview</h2>
            <div className="h-48 bg-[#050A15] rounded-xl viewer-grid flex flex-col items-center justify-center border border-navy-700/50 relative overflow-hidden">
              {/* Subtle grid background */}
              <div className="absolute inset-0 bg-[linear-gradient(to_right,#0ea5e905_1px,transparent_1px),linear-gradient(to_bottom,#0ea5e905_1px,transparent_1px)] bg-[size:20px_20px] pointer-events-none" />
              
              <div className="relative z-10 flex flex-col items-center justify-center">
                {isCompleted ? (
                  <>
                    <Check className="w-12 h-12 text-green-500 mb-3 drop-shadow-[0_0_10px_rgba(34,197,94,0.4)]" />
                    <p className="text-sm text-green-400 font-semibold tracking-wide">Model Generated Successfully</p>
                    <p className="text-[10px] uppercase tracking-widest text-slate-400 mt-1.5 font-bold">Vertex-Colored GLB Exported</p>
                  </>
                ) : (
                  <>
                    <Box className="w-12 h-12 text-cyan-500/20 mb-3 animate-pulse" />
                    <p className="text-xs text-slate-500 font-bold uppercase tracking-widest">3D preview will appear here</p>
                  </>
                )}
              </div>
            </div>
          </div>

          <div className="flex flex-wrap gap-3">
            <Link 
              to={`/viewer?jobId=${jobId}`} 
              className={`flex-1 min-w-[140px] text-center px-4 py-3 rounded-lg text-[10px] font-bold tracking-widest uppercase transition-all ${
                isCompleted 
                  ? 'bg-blue-600 hover:bg-blue-500 text-white shadow-[0_0_15px_rgba(37,99,235,0.4)]' 
                  : 'bg-[#050A15] text-slate-500 cursor-not-allowed border border-navy-700'
              }`}
              onClick={(e) => !isCompleted && e.preventDefault()}
            >
              View 3D Model
            </Link>
            <Link 
              to={`/accuracy/${jobId}`} 
              className={`flex-1 min-w-[140px] text-center px-4 py-3 rounded-lg text-[10px] font-bold tracking-widest uppercase transition-all ${
                isCompleted 
                  ? 'bg-[#050A15] hover:bg-navy-800 text-cyan-400 border border-cyan-500/30 hover:border-cyan-500/50' 
                  : 'bg-[#050A15] text-slate-600 border border-navy-700 cursor-not-allowed'
              }`}
              onClick={(e) => !isCompleted && e.preventDefault()}
            >
              View Accuracy
            </Link>
            {!isCompleted && !isFailed && !isCancelled && (
              <button disabled={isCancelling} onClick={cancelProcessing} className={`w-full px-4 py-3 border rounded-lg text-[10px] font-bold tracking-widest uppercase transition-colors ${isCancelling ? 'bg-slate-800/50 text-slate-500 border-slate-700' : 'bg-red-500/10 hover:bg-red-500/20 text-red-400 border-red-500/30'}`}>
                {isCancelling ? 'Cancelling...' : 'Cancel Processing'}
              </button>
            )}
            {(isFailed || isCancelled) && (
              <Link to="/reconstruction/new" className={`w-full text-center px-4 py-3 rounded-lg text-[10px] font-bold tracking-widest uppercase transition-colors ${isFailed ? 'bg-red-600 hover:bg-red-500 text-white shadow-[0_0_15px_rgba(220,38,38,0.4)]' : 'bg-blue-600 hover:bg-blue-500 text-white shadow-[0_0_15px_rgba(37,99,235,0.4)]'}`}>
                Start New Reconstruction
              </Link>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
