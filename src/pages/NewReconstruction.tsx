import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Upload, Film, CheckCircle2, ChevronRight, ChevronLeft, 
  Rocket, AlertTriangle, Monitor, Target, Zap, XCircle
} from 'lucide-react';
import { useSettings } from '../contexts/SettingsContext';
import { apiFetch, BACKEND_URL } from '../utils/api';
import { safeGetStorage } from '../utils/storage';

export default function NewReconstruction() {
  const navigate = useNavigate();
  const { settings } = useSettings();
  const [currentStep, setCurrentStep] = useState(1);
  const [quality, setQuality] = useState(settings.processingDefaults.qualityMode.toLowerCase().includes('fast') ? 'preview' : settings.processingDefaults.qualityMode.toLowerCase().includes('max') ? 'high' : 'standard');
  
  // Configuration State
  const [gpsEnabled, setGpsEnabled] = useState(true);
  const [imuEnabled, setImuEnabled] = useState(true);
  const [rtkPpkEnabled, setRtkPpkEnabled] = useState(false);
  const [cameraIntrinsics, setCameraIntrinsics] = useState('Auto-Detect');
  const [flightAltitude, setFlightAltitude] = useState<string>('120');
  const [outputs, setOutputs] = useState<Record<string, boolean>>({
    'Point Cloud': settings.processingDefaults.outputs.pointCloud,
    'Textured Mesh': settings.processingDefaults.outputs.texturedMesh,
    'Digital Surface Model': settings.processingDefaults.outputs.digitalSurfaceModel,
    'Orthographic Map': settings.processingDefaults.outputs.orthographicMap,
  });
  
  // Real Upload State
  const fileInputRef = useRef<HTMLInputElement>(null);
  const telemetryInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [telemetryFile, setTelemetryFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [isStarting, setIsStarting] = useState(false);

  const steps = [
    { id: 1, label: 'Upload' },
    { id: 2, label: 'Flight Data' },
    { id: 3, label: 'Configuration' },
    { id: 4, label: 'Review' }
  ];

  const formatSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) processFile(file);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleTelemetrySelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) setTelemetryFile(file);
    if (telemetryInputRef.current) telemetryInputRef.current.value = '';
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) processFile(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const processFile = (file: File) => {
    const validExts = ['.mp4', '.mov', '.avi'];
    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    
    if (!validExts.includes(ext)) {
      setUploadError(`Unsupported format: ${ext}. Please use MP4, MOV, or AVI.`);
      return;
    }
    
    if (file.size > 10 * 1024 * 1024 * 1024) { // 10 GB
      setUploadError('File is too large. Maximum size is 10 GB.');
      return;
    }

    setSelectedFile(file);
    setUploadError(null);
    setUploadProgress(0);
    setJobId(null);
  };

  const uploadFiles = () => {
    if (!selectedFile) return;
    setIsUploading(true);
    setUploadProgress(0);
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    if (telemetryFile) {
      formData.append('telemetry_file', telemetryFile);
    }

    const xhr = new XMLHttpRequest();
    
    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable) {
        const percentCompleted = Math.round((event.loaded * 100) / event.total);
        setUploadProgress(percentCompleted);
      }
    });

    xhr.addEventListener('load', () => {
      setIsUploading(false);
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const response = JSON.parse(xhr.responseText);
          setJobId(response.job_id);
          setUploadProgress(100);
        } catch (e) {
          setUploadError('Invalid response from server');
        }
      } else {
        try {
          const response = JSON.parse(xhr.responseText);
          setUploadError(response.detail || 'Upload failed');
        } catch (e) {
          setUploadError(`Upload failed with status ${xhr.status}`);
        }
      }
    });

    xhr.addEventListener('error', () => {
      setIsUploading(false);
      setUploadError('Network error occurred during upload. Is the backend running?');
    });

    xhr.open('POST', `${BACKEND_URL}/upload`, true);
    
    // Check for token in localStorage, then sessionStorage
    const localSession = safeGetStorage('aerorecon3d_auth_token');
    const tempSession = safeGetStorage('aerorecon3d_auth_token', true);
    const token = localSession || tempSession;
    if (token) {
      xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    }
    
    xhr.send(formData);
  };

  const handleNext = () => setCurrentStep(prev => Math.min(prev + 1, 4));
  const handleBack = () => setCurrentStep(prev => Math.max(prev - 1, 1));
  
  const handleStartReconstruction = () => {
    if (!jobId) return;
    setIsStarting(true);
    
    apiFetch(`/start/${jobId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        quality,
        gpsEnabled,
        imuEnabled,
        rtkPpkEnabled,
        cameraIntrinsics,
        flightAltitude: parseFloat(flightAltitude) || 120,
        outputs
      })
    })
      .then(async (res) => {
        setIsStarting(false);
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          alert(err.detail || 'Failed to start reconstruction');
          return;
        }
        navigate('/processing', { state: { jobId } });
      })
      .catch(() => {
        setIsStarting(false);
        alert('Network error starting reconstruction');
      });
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      {/* Steps Header */}
      <div className="flex items-center justify-between max-w-2xl mx-auto mb-10 relative">
        {steps.map((step, index) => {
          const isCompleted = currentStep > step.id;
          const isCurrent = currentStep === step.id;
          
          return (
            <React.Fragment key={step.id}>
              <div className="flex flex-col items-center relative z-10">
                <div className={`w-10 h-10 flex items-center justify-center rounded-full text-sm font-semibold transition-all duration-300
                  ${isCompleted ? 'bg-blue-600 text-white shadow-[0_0_15px_rgba(37,99,235,0.4)]' : ''}
                  ${isCurrent ? 'bg-cyan-500/20 text-cyan-400 ring-1 ring-cyan-500 shadow-[0_0_20px_rgba(34,211,238,0.2)]' : ''}
                  ${!isCompleted && !isCurrent ? 'bg-[#050A15] border border-navy-700 text-slate-500' : ''}
                `}>
                  {isCompleted ? <CheckCircle2 size={20} /> : step.id}
                </div>
                <span className={`absolute top-12 text-[10px] font-bold tracking-widest hidden sm:block whitespace-nowrap uppercase ${isCurrent ? 'text-cyan-400' : 'text-slate-500'}`}>
                  {step.label}
                </span>
              </div>
              {index < steps.length - 1 && (
                <div className={`h-[1px] flex-1 mx-4 transition-colors ${isCompleted ? 'bg-blue-600/50' : 'bg-navy-700'}`} />
              )}
            </React.Fragment>
          );
        })}
      </div>

      <div className="bg-[#0A1224] border border-navy-700/50 rounded-2xl p-6 md:p-10 shadow-sm relative overflow-hidden">
        {/* Subtle grid background */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#0ea5e905_1px,transparent_1px),linear-gradient(to_bottom,#0ea5e905_1px,transparent_1px)] bg-[size:20px_20px] pointer-events-none" />
        
        <div className="relative z-10">
        {currentStep === 1 && (
          <div>
            <h2 className="text-xl font-bold mb-2 text-slate-100 tracking-wide">Upload Drone Video</h2>
            <p className="text-slate-400 mb-8 text-sm">Select your UAV flight recording</p>
            
            <input 
              type="file"
              ref={fileInputRef}
              onChange={handleFileSelect}
              accept=".mp4,.mov,.avi"
              className="hidden"
            />
            
            <div 
              onClick={() => fileInputRef.current?.click()}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              className="border border-dashed border-navy-600/80 bg-[#050A15] rounded-xl p-8 md:p-12 text-center hover:border-cyan-500/40 hover:bg-cyan-500/5 transition-all duration-300 cursor-pointer group"
            >
              <Upload className="w-12 h-12 text-slate-600 mb-4 mx-auto group-hover:text-cyan-400 transition-colors" />
              <p className="text-slate-200 font-medium mb-1 tracking-wide">Drag and drop your drone video here</p>
              <p className="text-sm text-slate-500">or click to browse</p>
              <p className="text-[10px] font-mono text-slate-600 mt-6 tracking-widest uppercase">Supported: MP4, MOV, AVI • Max 10 GB</p>
            </div>

            {uploadError && (
              <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-4 mt-4 flex items-center gap-3">
                <XCircle className="w-5 h-5 text-red-400 shrink-0" />
                <p className="text-sm text-red-300">{uploadError}</p>
              </div>
            )}

            {selectedFile && !uploadError && (
              <div className="mt-6 space-y-4">
                <div className="bg-[#050A15] border border-navy-700 rounded-lg p-4 flex items-center gap-4 shadow-sm">
                  <div className="bg-blue-500/10 p-3 rounded-lg shrink-0 border border-blue-500/20">
                    <Film className="w-6 h-6 text-blue-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-slate-200 font-medium truncate tracking-wide" title={selectedFile.name}>{selectedFile.name}</p>
                    <p className="text-[10px] font-mono text-slate-400 mt-0.5">{formatSize(selectedFile.size)}</p>
                  </div>
                </div>
                
                <div className="pt-2">
                  <h3 className="text-sm font-semibold text-slate-200 mb-1 tracking-wide">Telemetry / Flight Log <span className="text-slate-500 font-normal text-xs ml-1">(Optional)</span></h3>
                  <input 
                    type="file"
                    ref={telemetryInputRef}
                    onChange={handleTelemetrySelect}
                    accept=".srt,.csv,.json"
                    className="hidden"
                  />
                  
                  {!telemetryFile ? (
                    <div 
                      onClick={() => telemetryInputRef.current?.click()}
                      className="border border-dashed border-navy-700 bg-[#050A15] rounded-lg p-5 text-center hover:border-cyan-500/40 hover:bg-cyan-500/5 transition-all cursor-pointer mt-3"
                    >
                      <p className="text-sm text-slate-300 font-medium">Click to attach DJI .SRT, .CSV, or .JSON</p>
                      <p className="text-[10px] text-amber-500/80 mt-2 tracking-wide uppercase max-w-sm mx-auto leading-relaxed">If no telemetry is provided, GPS/IMU telemetry is unavailable — reconstruction will use relative/local coordinates.</p>
                    </div>
                  ) : (
                    <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4 flex items-center justify-between mt-3">
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-green-400" />
                        <div>
                          <p className="text-sm font-medium text-slate-200 tracking-wide">{telemetryFile.name}</p>
                          <p className="text-[10px] font-bold tracking-widest text-green-400 uppercase mt-0.5">Telemetry Attached</p>
                        </div>
                      </div>
                      <button onClick={() => setTelemetryFile(null)} className="text-slate-500 hover:text-red-400 transition-colors">
                        <XCircle className="w-5 h-5" />
                      </button>
                    </div>
                  )}
                </div>

                {!jobId && !isUploading && (
                  <button 
                    onClick={uploadFiles}
                    className="w-full py-3.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-bold text-sm tracking-wide transition-all shadow-[0_0_15px_rgba(37,99,235,0.3)] hover:shadow-[0_0_20px_rgba(37,99,235,0.5)] mt-6"
                  >
                    CONFIRM & UPLOAD
                  </button>
                )}

                {isUploading && (
                  <div className="bg-navy-900 border border-navy-600/50 rounded-lg p-4 flex items-center gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-slate-300">Uploading files...</span>
                        <span className="text-blue-400 font-medium">{uploadProgress}%</span>
                      </div>
                      <div className="h-2 bg-navy-700 rounded-full overflow-hidden">
                        <div className="h-full bg-blue-500 transition-all duration-300" style={{ width: `${uploadProgress}%` }} />
                      </div>
                    </div>
                  </div>
                )}
                
                {jobId && !isUploading && (
                  <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4 flex items-center gap-3">
                    <CheckCircle2 className="w-5 h-5 text-green-400 shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-green-400">Upload Complete</p>
                      <p className="text-xs text-green-500/80">Job ID: {jobId}</p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {currentStep === 2 && (
          <div>
            <h2 className="text-xl font-bold mb-6 text-slate-100 tracking-wide">Flight Data Configuration</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="flex items-center justify-between p-4 bg-[#050A15] rounded-xl border border-navy-700 shadow-sm cursor-pointer hover:border-blue-500/50 transition-colors" onClick={() => setGpsEnabled(!gpsEnabled)}>
                <span className="text-sm font-medium text-slate-300">GPS Data</span>
                <div className={`w-11 h-6 rounded-full relative shadow-[0_0_10px_rgba(37,99,235,0.4)] transition-colors duration-300 ${gpsEnabled ? 'bg-blue-600' : 'bg-navy-800'}`}>
                  <div className={`w-5 h-5 bg-white rounded-full absolute top-0.5 shadow-sm transition-all duration-300 ${gpsEnabled ? 'right-0.5' : 'left-0.5'}`} />
                </div>
              </div>
              <div className="flex items-center justify-between p-4 bg-[#050A15] rounded-xl border border-navy-700 shadow-sm cursor-pointer hover:border-blue-500/50 transition-colors" onClick={() => setImuEnabled(!imuEnabled)}>
                <span className="text-sm font-medium text-slate-300">IMU Data</span>
                <div className={`w-11 h-6 rounded-full relative shadow-[0_0_10px_rgba(37,99,235,0.4)] transition-colors duration-300 ${imuEnabled ? 'bg-blue-600' : 'bg-navy-800'}`}>
                  <div className={`w-5 h-5 bg-white rounded-full absolute top-0.5 shadow-sm transition-all duration-300 ${imuEnabled ? 'right-0.5' : 'left-0.5'}`} />
                </div>
              </div>
              <div className="col-span-1 md:col-span-2 space-y-2">
                <label className="text-[11px] font-bold tracking-widest text-slate-400 uppercase">Camera Intrinsics</label>
                <select 
                  value={cameraIntrinsics}
                  onChange={(e) => setCameraIntrinsics(e.target.value)}
                  className="w-full bg-[#050A15] border border-navy-700 rounded-lg px-4 py-3 text-slate-200 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/30 transition-all cursor-pointer"
                >
                  <option>Auto-Detect</option>
                  <option>DJI Mavic 3</option>
                  <option>DJI Mini 4</option>
                  <option>Custom</option>
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-[11px] font-bold tracking-widest text-slate-400 uppercase">Flight Altitude</label>
                <div className="flex">
                  <input 
                    type="number" 
                    value={flightAltitude} 
                    onChange={(e) => setFlightAltitude(e.target.value)}
                    placeholder="e.g. 120"
                    className="w-full bg-[#050A15] border border-navy-700 border-r-0 rounded-l-lg px-4 py-3 text-slate-200 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/30 transition-all" 
                  />
                  <span className="bg-navy-800 border border-navy-700 rounded-r-lg px-4 py-3 text-slate-400 shrink-0 font-medium">m AGL</span>
                </div>
              </div>
              <div className="flex items-center justify-between p-4 bg-[#050A15] rounded-xl border border-navy-700 shadow-sm cursor-pointer hover:border-blue-500/50 transition-colors" onClick={() => setRtkPpkEnabled(!rtkPpkEnabled)}>
                <div>
                  <div className="text-sm font-medium text-slate-300">RTK/PPK</div>
                  <div className="text-[10px] text-slate-500 mt-0.5 tracking-wide">Post-processing kinematic correction</div>
                </div>
                <div className={`w-11 h-6 rounded-full relative shadow-[0_0_10px_rgba(37,99,235,0.4)] transition-colors duration-300 ${rtkPpkEnabled ? 'bg-blue-600' : 'bg-navy-800 border border-navy-600'}`}>
                  <div className={`w-5 h-5 bg-white rounded-full absolute top-0.5 shadow-sm transition-all duration-300 ${rtkPpkEnabled ? 'right-0.5' : 'left-0.5 bg-slate-400'}`} />
                </div>
              </div>
            </div>
          </div>
        )}

        {currentStep === 3 && (
          <div>
            <h2 className="text-xl font-bold mb-6 text-slate-100 tracking-wide">Processing Configuration</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
              <div 
                onClick={() => setQuality('preview')}
                className={`p-4 rounded-xl border cursor-pointer transition-all ${quality === 'preview' ? 'border-cyan-500 bg-cyan-500/10 shadow-[0_0_15px_rgba(34,211,238,0.15)]' : 'border-navy-700 hover:border-cyan-500/40 bg-[#050A15]'}`}
              >
                <Zap className={`w-6 h-6 mb-3 ${quality === 'preview' ? 'text-cyan-400' : 'text-slate-500'}`} />
                <h3 className="font-semibold text-slate-200 mb-1 tracking-wide">Preview</h3>
                <p className="text-[10px] font-mono text-cyan-400/80 mb-2">~15 MIN</p>
                <p className="text-[11px] text-slate-400 leading-relaxed">Lower resolution for quick review and verification.</p>
              </div>
              <div 
                onClick={() => setQuality('standard')}
                className={`p-4 rounded-xl border cursor-pointer transition-all relative ${quality === 'standard' ? 'border-blue-500 bg-blue-600/10 shadow-[0_0_15px_rgba(37,99,235,0.2)]' : 'border-navy-700 hover:border-blue-500/40 bg-[#050A15]'}`}
              >
                <div className="absolute top-3 right-3 bg-blue-600/20 text-blue-400 border border-blue-500/30 text-[9px] px-2 py-0.5 rounded-full font-bold uppercase tracking-widest">Recommended</div>
                <Monitor className={`w-6 h-6 mb-3 ${quality === 'standard' ? 'text-blue-400' : 'text-slate-500'}`} />
                <h3 className="font-semibold text-slate-200 mb-1 tracking-wide">Standard</h3>
                <p className="text-[10px] font-mono text-blue-400/80 mb-2">~1-2 HOURS</p>
                <p className="text-[11px] text-slate-400 leading-relaxed">Balanced performance and detail for most missions.</p>
              </div>
              <div 
                onClick={() => setQuality('high')}
                className={`p-4 rounded-xl border cursor-pointer transition-all ${quality === 'high' ? 'border-purple-500 bg-purple-500/10 shadow-[0_0_15px_rgba(168,85,247,0.15)]' : 'border-navy-700 hover:border-purple-500/40 bg-[#050A15]'}`}
              >
                <Target className={`w-6 h-6 mb-3 ${quality === 'high' ? 'text-purple-400' : 'text-slate-500'}`} />
                <h3 className="font-semibold text-slate-200 mb-1 tracking-wide">High Accuracy</h3>
                <p className="text-[10px] font-mono text-purple-400/80 mb-2">~3-5 HOURS</p>
                <p className="text-[11px] text-slate-400 leading-relaxed">Research-grade precision and maximum dense point cloud.</p>
              </div>
            </div>

            <h3 className="text-[11px] font-bold tracking-widest text-slate-400 uppercase mb-3">Output Formats</h3>
            <div className="space-y-3 bg-[#050A15] p-5 rounded-xl border border-navy-700 shadow-sm">
              {['Point Cloud', 'Textured Mesh', 'Digital Surface Model', 'Orthographic Map'].map((item) => (
                <label key={item} className="flex items-center gap-3 cursor-pointer group">
                  <input 
                    type="checkbox" 
                    checked={outputs[item] || false} 
                    onChange={(e) => setOutputs({...outputs, [item]: e.target.checked})}
                    className="appearance-none w-5 h-5 border-2 border-navy-600 rounded bg-navy-900 checked:bg-cyan-500 checked:border-cyan-500 cursor-pointer flex items-center justify-center after:content-['✓'] after:text-navy-900 after:font-bold after:text-xs after:hidden checked:after:block transition-all" 
                  />
                  <span className="text-sm text-slate-300 group-hover:text-slate-100 transition-colors tracking-wide">{item}</span>
                </label>
              ))}
            </div>
          </div>
        )}

        {currentStep === 4 && (
          <div>
            <h2 className="text-xl font-bold mb-6 text-slate-100 tracking-wide">Review & Start</h2>
            
            <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4 mb-6 flex items-start gap-3 shadow-sm">
              <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
              <p className="text-sm text-amber-200/90 leading-relaxed font-medium">
                Reconstruction will now process on the real backend. You will be redirected to the processing view.
              </p>
            </div>

            <div className="space-y-4">
              <div className="bg-[#050A15] border border-navy-700 rounded-xl p-5 shadow-sm">
                <h4 className="text-[10px] font-bold text-cyan-500 uppercase tracking-widest mb-3">Video Source</h4>
                <div className="flex items-center gap-3">
                  <div className="bg-blue-500/10 p-2.5 rounded-lg border border-blue-500/20">
                    <Film className="w-5 h-5 text-blue-400" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-slate-200 tracking-wide">{selectedFile?.name || 'No file selected'}</div>
                    <div className="text-[10px] font-mono text-slate-400 mt-0.5">{selectedFile ? formatSize(selectedFile.size) : ''} {jobId ? `• JOB: ${jobId}` : ''}</div>
                  </div>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-[#050A15] border border-navy-700 rounded-xl p-5 shadow-sm">
                  <h4 className="text-[10px] font-bold text-cyan-500 uppercase tracking-widest mb-4">Flight Data</h4>
                  <ul className="text-xs space-y-3 text-slate-300 font-medium">
                    <li className="flex justify-between items-center"><span className="text-slate-500">GPS Data</span><span className={`px-2 py-0.5 rounded uppercase tracking-widest text-[9px] ${gpsEnabled ? 'text-green-400 bg-green-500/10 border border-green-500/20' : 'text-slate-400 bg-navy-800 border border-navy-700'}`}>{gpsEnabled ? 'Enabled' : 'Disabled'}</span></li>
                    <li className="flex justify-between items-center"><span className="text-slate-500">IMU Data</span><span className={`px-2 py-0.5 rounded uppercase tracking-widest text-[9px] ${imuEnabled ? 'text-green-400 bg-green-500/10 border border-green-500/20' : 'text-slate-400 bg-navy-800 border border-navy-700'}`}>{imuEnabled ? 'Enabled' : 'Disabled'}</span></li>
                    <li className="flex justify-between items-center"><span className="text-slate-500">Camera</span><span className="text-slate-300">{cameraIntrinsics}</span></li>
                    <li className="flex justify-between items-center"><span className="text-slate-500">Altitude</span><span className="font-mono">{flightAltitude}m AGL</span></li>
                    <li className="flex justify-between items-center"><span className="text-slate-500">RTK/PPK</span><span className={`px-2 py-0.5 rounded uppercase tracking-widest text-[9px] ${rtkPpkEnabled ? 'text-purple-400 bg-purple-500/10 border border-purple-500/20' : 'text-slate-400 bg-navy-800 border border-navy-700'}`}>{rtkPpkEnabled ? 'Enabled' : 'Disabled'}</span></li>
                  </ul>
                </div>
                <div className="bg-[#050A15] border border-navy-700 rounded-xl p-5 shadow-sm">
                  <h4 className="text-[10px] font-bold text-cyan-500 uppercase tracking-widest mb-4">Configuration</h4>
                  <ul className="text-xs space-y-3 text-slate-300 font-medium">
                    <li className="flex justify-between items-center"><span className="text-slate-500">Quality</span><span className="uppercase tracking-widest text-[10px] bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2 py-0.5 rounded">{quality}</span></li>
                    <li className="flex justify-between items-center"><span className="text-slate-500">Outputs</span><span className="text-slate-300">{Object.values(outputs).filter(Boolean).length} Selected</span></li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

            <div className="flex justify-between mt-8 pt-6 border-t border-navy-700/50">
          <button 
            onClick={handleBack}
            disabled={currentStep === 1}
            className={`px-4 py-2.5 rounded-lg font-bold text-xs tracking-wide uppercase transition-colors flex items-center gap-2 ${currentStep === 1 ? 'opacity-0 pointer-events-none' : 'text-slate-400 hover:bg-[#050A15] hover:text-slate-200 border border-navy-700 shadow-sm'}`}
          >
            <ChevronLeft size={16} /> Back
          </button>
          
          {currentStep < 4 ? (
            <button 
              onClick={handleNext}
              disabled={currentStep === 1 && !jobId}
              className={`px-6 py-2.5 rounded-lg font-bold text-xs tracking-wide uppercase transition-all flex items-center gap-2 ${
                currentStep === 1 && !jobId 
                ? 'bg-navy-800 text-slate-500 cursor-not-allowed border border-navy-700' 
                : 'bg-blue-600 hover:bg-blue-500 text-white shadow-[0_0_15px_rgba(37,99,235,0.3)] hover:shadow-[0_0_20px_rgba(37,99,235,0.5)]'
              }`}
            >
              Continue <ChevronRight size={16} />
            </button>
          ) : (
            <button 
              onClick={handleStartReconstruction}
              disabled={isStarting}
              className="px-6 py-2.5 rounded-lg font-bold text-xs tracking-wide uppercase transition-all flex items-center gap-2 bg-cyan-600 hover:bg-cyan-500 text-white shadow-[0_0_15px_rgba(8,145,178,0.4)] hover:shadow-[0_0_20px_rgba(8,145,178,0.6)]"
            >
              {isStarting ? (
                <>Starting backend...</>
              ) : (
                <>
                  <Rocket size={16} /> Start Processing
                </>
              )}
            </button>
          )}
        </div>
        </div>
      </div>
    </div>
  );
}
