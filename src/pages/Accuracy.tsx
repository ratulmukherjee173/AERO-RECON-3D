import { useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { safeGetStorage } from '../utils/storage';
import { 
  ArrowLeft, Download, Target
} from 'lucide-react';

export default function Accuracy() {
  const { id } = useParams();
  const navigate = useNavigate();

  useEffect(() => {
    if (!id) {
      const lastJob = safeGetStorage('last_job_id');
      if (lastJob) {
        navigate(`/accuracy/${lastJob}`, { replace: true });
      }
    }
  }, [id, navigate]);

  if (!id && !safeGetStorage('last_job_id')) {
    return (
      <div className="h-[calc(100vh-theme(spacing.16))] flex flex-col items-center justify-center text-center px-4 -m-4 sm:-m-6 lg:-m-8">
        <Target className="w-16 h-16 text-slate-600 mb-4" />
        <h2 className="text-2xl font-bold text-slate-200 mb-2">No Accuracy Analysis Available</h2>
        <p className="text-slate-400 max-w-md">
          You haven't processed any reconstruction jobs yet. 
          Upload a video to generate an accuracy report.
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-2">
        <div className="flex items-center gap-4">
          <Link to={`/projects`} className="p-2 hover:bg-navy-800 rounded-lg text-slate-400 hover:text-slate-200 transition-colors">
            <ArrowLeft size={20} />
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl md:text-2xl font-bold text-slate-100">Accuracy Analysis</h1>
            </div>
            <p className="text-slate-400 text-sm mt-1 font-mono">Job ID: {id}</p>
          </div>
        </div>
        <button onClick={() => alert('Exporting report...')} className="px-4 py-2 bg-navy-800 hover:bg-navy-700 border border-navy-600 text-slate-200 rounded-lg text-sm font-medium transition-colors flex items-center gap-2">
          <Download size={16} /> Export Report
        </button>
      </div>

      <div className="bg-navy-800 border border-navy-700 border-dashed rounded-xl p-12 flex flex-col items-center justify-center text-center mt-12">
        <Target className="w-12 h-12 text-slate-600 mb-4" />
        <h2 className="text-xl font-bold text-slate-300 mb-2">Metric accuracy unavailable</h2>
        <p className="text-slate-500 max-w-md">
          Ground truth required. The current reconstruction pipeline does not include real metric reference data or ground control points (GCPs).
        </p>
      </div>

    </div>
  );
}
