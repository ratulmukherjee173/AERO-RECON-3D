import { Plus, FileText, Download, Eye, Trash2, FolderKanban } from 'lucide-react';
import { useState, useEffect } from 'react';
import { formatDate } from '../utils';
import { apiFetch } from '../utils/api';

interface JobSummary {
  job_id: string;
  project_id: string | null;
  status: string;
  created_at: string;
  report_path?: string | null;
}

export default function Reports() {
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchReports = () => {
    setLoading(true);
    apiFetch('/jobs')
      .then(res => (res.ok ? res.json() : []))
      .then((data: JobSummary[]) => {
         const successJobs = (data || []).filter(j => j.status === 'SUCCESS');
         const mapped = successJobs.map(j => ({
            id: j.job_id,
            type: 'Quality Report',
            projectName: j.project_id || j.job_id,
            generatedDate: j.created_at,
            status: j.report_path ? 'ready' : 'not generated'
         }));
         setReports(mapped);
      })
      .catch(() => setReports([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const [generating, setGenerating] = useState<string | null>(null);

  const handleGenerate = async (id: string) => {
    setGenerating(id);
    try {
      const res = await apiFetch(`/reports/${id}/generate`, { method: 'POST' });
      if (!res.ok) {
        alert("Report generation failed. Please try again.");
      }
      fetchReports();
    } catch (e) {
      alert("Report service unavailable.");
    } finally {
      setGenerating(null);
    }
  };

  const handleAction = async (action: string, id: string) => {
    if (action === 'Delete') {
      alert("Report deletion is unavailable.");
      return;
    }

    const report = reports.find(r => r.id === id);
    if (!report || report.status !== 'ready') {
      alert("Report not generated yet.");
      return;
    }

    try {
      const res = await apiFetch(`/reports/${id}/download`);
      if (!res.ok) {
        alert("Report file not found.");
        return;
      }
      
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      
      if (action === 'View') {
        window.open(url, '_blank');
      } else if (action === 'Download') {
        const a = document.createElement('a');
        a.href = url;
        a.download = `aerorecon_${id}_report.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      }
      
      setTimeout(() => window.URL.revokeObjectURL(url), 1000);
    } catch (e) {
      alert("Failed to access report.");
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-2">
        <h1 className="text-xl md:text-2xl font-bold text-slate-100">Reports</h1>
        <div className="flex gap-2 invisible">
          <Plus size={16} /> 
        </div>
      </div>

      <div className="bg-navy-800 border border-navy-600/50 rounded-xl overflow-hidden">
        {/* Desktop Table */}
        <div className="hidden md:block overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-slate-400 uppercase bg-navy-900/80 border-b border-navy-700">
              <tr>
                <th className="px-6 py-4 font-medium">Type</th>
                <th className="px-6 py-4 font-medium">Project</th>
                <th className="px-6 py-4 font-medium">Date Generated</th>
                <th className="px-6 py-4 font-medium">Accuracy</th>
                <th className="px-6 py-4 font-medium">Status</th>
                <th className="px-6 py-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-navy-700/50 text-slate-300">
              {reports.length === 0 && !loading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-slate-400">
                    <FolderKanban className="w-8 h-8 text-slate-600 mx-auto mb-3" />
                    No reports generated yet.
                  </td>
                </tr>
              ) : (
                reports.map((report) => (
                  <tr key={report.id} className="hover:bg-navy-700/30 transition-colors group">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-blue-400" />
                        <span className="font-medium text-slate-200">{report.type}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">{report.projectName}</td>
                    <td className="px-6 py-4 text-slate-400">{formatDate(report.generatedDate)}</td>
                    <td className="px-6 py-4">
                      <span className="text-slate-500 text-xs tracking-wide">UNAVAILABLE</span>
                    </td>
                    <td className="px-6 py-4">
                      {report.status === 'ready' ? (
                        <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-green-500/10 text-green-400">
                          Ready
                        </span>
                      ) : generating === report.id ? (
                        <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400">
                          Generating...
                        </span>
                      ) : (
                        <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-slate-500/10 text-slate-400">
                          Not Generated
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center justify-end gap-2 opacity-100 transition-opacity">
                        {report.status !== 'ready' && generating !== report.id && (
                          <button onClick={() => handleGenerate(report.id)} className="px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white text-xs rounded transition-colors">
                            Generate
                          </button>
                        )}
                        <button onClick={() => handleAction('View', report.id)} className="p-1.5 text-slate-400 hover:text-blue-400 hover:bg-blue-500/10 rounded" title="View"><Eye size={16} /></button>
                        <button onClick={() => handleAction('Download', report.id)} className="p-1.5 text-slate-400 hover:text-green-400 hover:bg-green-500/10 rounded" title="Download"><Download size={16} /></button>
                        <button onClick={() => handleAction('Delete', report.id)} className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded" title="Delete"><Trash2 size={16} /></button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Mobile Cards */}
        <div className="md:hidden divide-y divide-navy-700/50">
          {reports.length === 0 && !loading ? (
            <div className="p-8 text-center text-slate-400">
              <FolderKanban className="w-8 h-8 text-slate-600 mx-auto mb-3" />
              No reports generated yet.
            </div>
          ) : (
            reports.map((report) => (
              <div key={report.id} className="p-4 space-y-3">
                <div className="flex justify-between items-start">
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-blue-400" />
                    <span className="font-medium text-slate-200">{report.type}</span>
                  </div>
                  {report.status === 'ready' ? (
                    <span className="px-2 py-0.5 rounded text-xs font-medium bg-green-500/10 text-green-400">
                      Ready
                    </span>
                  ) : generating === report.id ? (
                    <span className="px-2 py-0.5 rounded text-xs font-medium bg-blue-500/10 text-blue-400">
                      Generating...
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 rounded text-xs font-medium bg-slate-500/10 text-slate-400">
                      Not Generated
                    </span>
                  )}
                </div>
                <div>
                  <div className="text-sm font-medium text-slate-300">{report.projectName}</div>
                  <div className="text-xs text-slate-500 mt-1">{formatDate(report.generatedDate)}</div>
                </div>
                <div className="flex justify-between items-center pt-2">
                  <span className="text-xs text-slate-500 tracking-wide">
                    ACCURACY UNAVAILABLE
                  </span>
                  <div className="flex items-center gap-3">
                    {report.status !== 'ready' && generating !== report.id && (
                      <button onClick={() => handleGenerate(report.id)} className="px-2 py-1 bg-blue-600 text-white text-xs rounded">
                        Generate
                      </button>
                    )}
                    <button onClick={() => handleAction('View', report.id)} className="text-slate-400 hover:text-blue-400"><Eye size={18} /></button>
                    <button onClick={() => handleAction('Download', report.id)} className="text-slate-400 hover:text-green-400"><Download size={18} /></button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
