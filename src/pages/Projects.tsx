import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Plus, Search, ChevronRight, SearchX } from 'lucide-react';
import { cn, formatDate, getStatusColor, getStatusLabel } from '../utils';
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
  created_at: string;
}

const StatusBadge = ({ status }: { status: string }) => {
  const colorClass = getStatusColor(status);
  const label = getStatusLabel(status);
  return (
    <span className={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium border uppercase tracking-wider", colorClass)}>
      {label}
    </span>
  );
};

export default function Projects() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState('All');
  
  const [projects, setProjects] = useState<Project[]>([]);
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [loading, setLoading] = useState(true);

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
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const getProjectStatus = (projectId: string) => {
    const projectJobs = jobs.filter(j => j.project_id === projectId);
    if (projectJobs.length === 0) return 'NONE';
    
    // Determine overall project status based on job history
    if (projectJobs.some(j => j.status === 'SUCCESS')) return 'SUCCESS';
    if (projectJobs.some(j => j.status === 'FAILED')) return 'FAILED';
    if (projectJobs.some(j => j.status === 'CANCELLED')) return 'CANCELLED';
    
    // Check active jobs
    const activeJobs = projectJobs.filter(j => ['UPLOADED', 'QUEUED', 'RUNNING'].includes(j.status));
    if (activeJobs.length > 0) {
      if (activeJobs.some(j => j.status === 'RUNNING')) return 'RUNNING';
      if (activeJobs.some(j => j.status === 'QUEUED')) return 'QUEUED';
      return 'UPLOADED';
    }
    
    return projectJobs[0].status;
  };

  const filteredProjects = projects
    .filter(p => {
      const matchesSearch = p.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
                            (p.description || '').toLowerCase().includes(searchTerm.toLowerCase());
      const pStatus = getProjectStatus(p.id);
      const matchesFilter = filter === 'All' || 
                           (filter === 'Processing' && ['QUEUED', 'RUNNING'].includes(pStatus)) ||
                           (filter === 'Completed' && pStatus === 'SUCCESS') ||
                           (filter === 'Failed' && pStatus === 'FAILED') ||
                           (filter === 'Cancelled' && pStatus === 'CANCELLED');
      return matchesSearch && matchesFilter;
    })
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

  if (loading) {
    return <div className="p-8 text-slate-400 text-center">Loading projects...</div>;
  }

  return (
    <div className="w-full">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
        <h1 className="text-2xl md:text-3xl font-bold text-slate-100 tracking-tight">Projects</h1>
        <Link 
          to="/reconstruction/new"
          className="bg-blue-600 hover:bg-blue-500 text-white px-5 py-2.5 rounded-lg text-xs font-bold tracking-widest uppercase flex items-center justify-center gap-2 transition-all w-full sm:w-auto shadow-[0_0_15px_rgba(37,99,235,0.3)] hover:shadow-[0_0_20px_rgba(37,99,235,0.5)]"
        >
          <Plus className="w-4 h-4" />
          New Reconstruction
        </Link>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-6">
        <div className="relative w-full sm:w-72">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input 
            type="text" 
            placeholder="Search projects..." 
            className="w-full bg-[#050A15] border border-navy-700 rounded-lg pl-9 pr-4 py-2.5 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/30 transition-all shadow-sm"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="flex bg-[#050A15] border border-navy-700/50 rounded-lg p-1 overflow-x-auto shadow-sm hide-scrollbar">
          {['All', 'Processing', 'Completed', 'Failed', 'Cancelled'].map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={cn(
                "px-4 py-1.5 rounded-md text-[11px] font-bold tracking-wider uppercase whitespace-nowrap transition-all",
                filter === f 
                  ? "bg-cyan-500/10 text-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.2)]" 
                  : "text-slate-400 hover:text-slate-200 hover:bg-navy-800/50"
              )}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Project Grid */}
      {filteredProjects.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filteredProjects.map((project) => {
            const pStatus = getProjectStatus(project.id);
            const statusColor = 
              pStatus === 'SUCCESS' ? 'bg-green-500' :
              pStatus === 'FAILED' ? 'bg-red-500' :
              (pStatus === 'RUNNING' || pStatus === 'QUEUED' || pStatus === 'UPLOADED') ? 'bg-blue-500' : 'bg-slate-500';

            return (
              <div 
                key={project.id}
                onClick={() => navigate(`/projects/${project.id}`)}
                className="bg-[#0A1224] border border-navy-700/50 rounded-xl overflow-hidden hover:border-cyan-500/40 transition-all cursor-pointer flex flex-col group shadow-sm relative"
              >
                <div className={cn("h-1 w-full absolute top-0 left-0", statusColor)} />
                {/* Subtle grid background */}
                <div className="absolute inset-0 bg-[linear-gradient(to_right,#0ea5e905_1px,transparent_1px),linear-gradient(to_bottom,#0ea5e905_1px,transparent_1px)] bg-[size:10px_10px] pointer-events-none" />
                
                <div className="p-6 flex-1 flex flex-col relative z-10">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-semibold text-base text-slate-100 flex items-center flex-wrap gap-2 group-hover:text-cyan-400 transition-colors tracking-wide">
                      {project.name}
                    </h3>
                  </div>
                  <div className="text-xs text-slate-400 mb-6 line-clamp-2 leading-relaxed">
                    {project.description || 'No description provided.'}
                  </div>
                  
                  <div className="mt-auto pt-4 border-t border-navy-700/50 flex justify-between items-center">
                    <div className="flex items-center gap-3">
                      {pStatus !== 'NONE' ? <StatusBadge status={pStatus} /> : <span className="text-xs text-slate-500 uppercase tracking-wider font-medium">No Jobs</span>}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] text-slate-500 font-mono tracking-wider">{formatDate(project.created_at)}</span>
                      <ChevronRight className="w-4 h-4 text-cyan-500/50 group-hover:text-cyan-400 transition-colors" />
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="bg-navy-800/50 p-4 rounded-full mb-4">
            <SearchX className="w-8 h-8 text-slate-500" />
          </div>
          <h3 className="text-lg font-medium text-slate-200 mb-1">
            {searchTerm ? "No matching projects found" : 
             filter === 'Processing' ? "No projects currently processing" : 
             filter === 'Completed' ? "No completed projects yet" : 
             filter === 'Failed' ? "No failed projects" : 
             "No projects found"}
          </h3>
          <p className="text-slate-400">
            {searchTerm ? "Try adjusting your search or filters" : 
             filter === 'All' ? "Create your first reconstruction project to get started." : 
             "Try adjusting your filters or create a new project."}
          </p>
        </div>
      )}
    </div>
  );
}
