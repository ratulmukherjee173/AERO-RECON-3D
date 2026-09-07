import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Plane, Cpu, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';
import { mockProjectDetails } from '../data/mock';
import { cn, formatDate, formatNumber, getStatusColor, getStatusLabel } from '../utils';

// Fallback components if missing
const DemoBadge = () => (
  <span className="ml-2 inline-flex items-center rounded-full bg-blue-500/10 px-2 py-0.5 text-xs font-medium text-blue-400 ring-1 ring-inset ring-blue-500/20">
    Demo
  </span>
);

const StatusBadge = ({ status }: { status: string }) => {
  const colorClass = getStatusColor ? getStatusColor(status) : 'bg-slate-500/10 text-slate-400 ring-slate-500/20';
  const label = getStatusLabel ? getStatusLabel(status) : status;
  return (
    <span className={cn("inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset", colorClass)}>
      {label}
    </span>
  );
};

export default function ProjectDetails() {
  const { id } = useParams<{ id: string }>();
  
  // Find project in mockProjectDetails array or object
  const project = Array.isArray(mockProjectDetails) 
    ? mockProjectDetails.find(p => p.id === id)
    : mockProjectDetails?.[id as keyof typeof mockProjectDetails];

  if (!project) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <AlertTriangle className="w-12 h-12 text-amber-500 mb-4" />
        <h2 className="text-xl font-bold text-slate-200 mb-2">Project Not Found</h2>
        <p className="text-slate-400 mb-6">The project you are looking for does not exist or has been removed.</p>
        <Link 
          to="/projects"
          className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg font-medium transition-colors"
        >
          Return to Projects
        </Link>
      </div>
    );
  }

  const isCompleted = project.status === 'completed';
  const isProcessing = project.status === 'processing';
  const isFailed = project.status === 'failed';
  const isPending = project.status === 'pending';

  return (
    <div className="w-full">
      {/* Header */}
      <div className="mb-6">
        <Link 
          to="/projects"
          className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-slate-200 mb-4 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Projects
        </Link>
        
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div className="flex items-center flex-wrap gap-3">
            <h1 className="text-xl md:text-2xl font-bold text-slate-100">{project.name}</h1>
            <StatusBadge status={project.status} />
            {project.isDemo && <DemoBadge />}
          </div>
          
          <div className="grid grid-cols-2 md:flex gap-3 w-full md:w-auto mt-4 md:mt-0">
            <Link 
              to={`/viewer/${project.id}`}
              className={cn(
                "px-4 py-2 rounded-lg font-medium text-sm flex justify-center items-center text-white bg-blue-600 hover:bg-blue-500 transition-colors",
                !isCompleted && "opacity-50 cursor-not-allowed pointer-events-none"
              )}
            >
              Open 3D Model
            </Link>
            <Link 
              to={`/accuracy/${project.id}`}
              className={cn(
                "px-4 py-2 rounded-lg font-medium text-sm flex justify-center items-center border border-navy-500 text-slate-200 hover:bg-navy-800 transition-colors",
                !isCompleted && "opacity-50 cursor-not-allowed pointer-events-none"
              )}
            >
              View Accuracy
            </Link>
            <Link 
              to={`/processing`}
              className="px-4 py-2 rounded-lg font-medium text-sm flex justify-center items-center text-slate-300 hover:bg-navy-800 transition-colors"
            >
              View Processing
            </Link>
            <button 
              onClick={() => alert("Generating report...")}
              className="px-4 py-2 rounded-lg font-medium text-sm flex justify-center items-center bg-navy-700 text-slate-200 hover:bg-navy-600 transition-colors"
              disabled={!isCompleted}
            >
              Generate Report
            </button>
          </div>
        </div>
      </div>

      {/* Info Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Flight Information */}
        <div className="bg-navy-800 border border-navy-600/50 rounded-xl p-5">
          <h2 className="font-semibold text-slate-100 mb-4 flex items-center gap-2">
            <Plane className="w-5 h-5 text-blue-400" />
            Flight Information
          </h2>
          <div className="grid grid-cols-2 gap-y-4">
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Location</p>
              <p className="text-sm font-medium text-slate-200">{project.flightInfo?.location || project.location || 'Unknown'}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Flight Date</p>
              <p className="text-sm font-medium text-slate-200">
                {formatDate ? formatDate(project.flightInfo?.date || project.date || project.createdAt) : (project.flightInfo?.date || project.date || project.createdAt)}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Flight Duration</p>
              <p className="text-sm font-medium text-slate-200">{project.flightInfo?.duration || '—'}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Video Resolution</p>
              <p className="text-sm font-medium text-slate-200">{project.flightInfo?.resolution || '—'}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Flight Altitude</p>
              <p className="text-sm font-medium text-slate-200">{project.flightInfo?.altitude || '—'}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Area Covered</p>
              <p className="text-sm font-medium text-slate-200">{project.flightInfo?.area || '—'}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">GPS Available</p>
              <div className="flex items-center gap-1.5">
                {project.flightInfo?.gps ? (
                  <><CheckCircle2 className="w-4 h-4 text-green-500" /><span className="text-sm font-medium text-slate-200">Yes</span></>
                ) : (
                  <><XCircle className="w-4 h-4 text-red-500" /><span className="text-sm font-medium text-slate-200">No</span></>
                )}
              </div>
            </div>
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">IMU Available</p>
              <div className="flex items-center gap-1.5">
                {project.flightInfo?.imu ? (
                  <><CheckCircle2 className="w-4 h-4 text-green-500" /><span className="text-sm font-medium text-slate-200">Yes</span></>
                ) : (
                  <><XCircle className="w-4 h-4 text-red-500" /><span className="text-sm font-medium text-slate-200">No</span></>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Processing Summary */}
        <div className="bg-navy-800 border border-navy-600/50 rounded-xl p-5">
          <h2 className="font-semibold text-slate-100 mb-4 flex items-center gap-2">
            <Cpu className="w-5 h-5 text-purple-400" />
            Processing Summary
          </h2>
          <div className="grid grid-cols-2 gap-y-4">
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Total Frames</p>
              <p className="text-sm font-medium text-slate-200">
                {formatNumber ? formatNumber(project.processing?.frames || 0) : (project.processing?.frames || 0)}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Camera Poses</p>
              <p className="text-sm font-medium text-slate-200">
                {formatNumber ? formatNumber(project.processing?.poses || 0) : (project.processing?.poses || 0)}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Point Cloud Points</p>
              <p className="text-sm font-medium text-slate-200">
                {formatNumber ? formatNumber(project.processing?.points || 0) : (project.processing?.points || 0)}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Model Size</p>
              <p className="text-sm font-medium text-slate-200">{project.processing?.size || '—'}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Processing Time</p>
              <p className="text-sm font-medium text-slate-200">{project.processing?.time || '—'}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Model Info */}
      <div className="bg-navy-800 border border-navy-600/50 rounded-xl p-5 mb-6">
        <h2 className="font-semibold text-slate-100 mb-4">Model Information</h2>
        
        {isCompleted && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-navy-900/50 rounded-lg p-4">
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Point Cloud Points</p>
              <p className="text-xl font-bold text-slate-200">
                {formatNumber ? formatNumber(project.processing?.points || 0) : (project.processing?.points || 0)}
              </p>
            </div>
            <div className="bg-navy-900/50 rounded-lg p-4">
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Model Size</p>
              <p className="text-xl font-bold text-slate-200">{project.processing?.size || '—'}</p>
            </div>
            <div className="bg-navy-900/50 rounded-lg p-4">
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Processing Time</p>
              <p className="text-xl font-bold text-slate-200">{project.processing?.time || '—'}</p>
            </div>
          </div>
        )}

        {isProcessing && (
          <div className="py-4">
            <div className="flex justify-between text-sm mb-2">
              <span className="text-blue-400 font-medium">Processing in progress...</span>
              <span className="text-slate-300">{project.progress || 0}%</span>
            </div>
            <div className="w-full bg-navy-900 rounded-full h-2.5 overflow-hidden">
              <div 
                className="bg-blue-500 h-2.5 rounded-full transition-all duration-500 ease-out"
                style={{ width: `${project.progress || 0}%` }}
              ></div>
            </div>
          </div>
        )}

        {isFailed && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 flex items-start gap-3 text-red-400">
            <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
            <div>
              <p className="font-medium">Processing Failed</p>
              <p className="text-sm mt-1 opacity-80">{project.error || 'An unknown error occurred during processing.'}</p>
            </div>
          </div>
        )}

        {isPending && (
          <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-4 flex items-start gap-3 text-amber-400">
            <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
            <div>
              <p className="font-medium">Waiting to begin processing</p>
              <p className="text-sm mt-1 opacity-80">Your reconstruction is queued and will start shortly.</p>
            </div>
          </div>
        )}
      </div>

      {/* Accuracy Card */}
      {isCompleted && (
        <div className="bg-navy-800 border border-navy-600/50 rounded-xl p-5">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h2 className="font-semibold text-slate-100">Reconstruction Confidence</h2>
              <p className="text-sm text-slate-400 mt-1">Based on keypoint matching and camera pose estimation</p>
            </div>
            <Link 
              to={`/accuracy/${project.id}`}
              className="text-blue-400 text-sm hover:text-blue-300 transition-colors"
            >
              View Full Analysis →
            </Link>
          </div>
          
          <div className="flex items-center gap-6">
            <div className={cn(
              "text-3xl font-bold",
              (project.accuracy || 0) >= 90 ? "text-green-400" : (project.accuracy || 0) >= 80 ? "text-amber-400" : "text-red-400"
            )}>
              {project.accuracy || 0}%
            </div>
            <div className="flex-1 max-w-md">
              <div className="w-full bg-navy-900 rounded-full h-2 overflow-hidden">
                <div 
                  className={cn(
                    "h-2 rounded-full",
                    (project.accuracy || 0) >= 90 ? "bg-green-500" : (project.accuracy || 0) >= 80 ? "bg-amber-500" : "bg-red-500"
                  )}
                  style={{ width: `${project.accuracy || 0}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
