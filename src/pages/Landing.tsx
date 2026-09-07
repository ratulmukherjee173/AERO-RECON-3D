import React from 'react';
import { Link } from 'react-router-dom';
import logoImg from '../assets/logo.png';
import { 
  Rocket, 
  Play, 
  Video, 
  Film, 
  Camera, 
  Layers, 
  Navigation, 
  Sparkles, 
  Box, 
  Target,
  ScanLine,
  Brain,
  MapPin,
  Monitor,
  AlertTriangle,
  Building2,
  Map,
  Hammer,
  Mountain
} from 'lucide-react';

const Landing: React.FC = () => {
  const steps = [
    { icon: Video, name: "Drone Video", desc: "Capture aerial footage" },
    { icon: Film, name: "Frame Processing", desc: "Extract & analyze frames" },
    { icon: Camera, name: "Camera Pose", desc: "Estimate camera positions" },
    { icon: Layers, name: "Depth Estimation", desc: "Generate depth maps" },
    { icon: Navigation, name: "GPS / IMU Fusion", desc: "Align spatial data" },
    { icon: Sparkles, name: "Point Cloud", desc: "Generate 3D points" },
    { icon: Box, name: "3D Model", desc: "Build textured mesh" },
    { icon: Target, name: "Accuracy Validation", desc: "Verify precision" }
  ];

  const whyCards = [
    { icon: ScanLine, title: "Single-Pass UAV Mapping", desc: "Complete 3D reconstruction from a single drone flight pass." },
    { icon: Brain, title: "AI-Powered Reconstruction", desc: "Deep learning models for accurate depth estimation and camera pose recovery." },
    { icon: MapPin, title: "Geospatial Accuracy", desc: "Georeferenced output with centimeter-level precision and validation." },
    { icon: Monitor, title: "Interactive 3D Visualization", desc: "Explore, measure, and analyze reconstructed models interactively." }
  ];

  const useCases = [
    { icon: AlertTriangle, title: "Disaster Assessment", desc: "Rapid damage mapping for emergency response." },
    { icon: Building2, title: "Infrastructure Inspection", desc: "Bridge and utility condition monitoring." },
    { icon: Map, title: "Urban Mapping", desc: "High-fidelity 3D city models for planning." },
    { icon: Hammer, title: "Construction Monitoring", desc: "Track progress against design models." },
    { icon: Mountain, title: "Terrain Analysis", desc: "Topographic surveys and change detection." }
  ];

  return (
    <div className="min-h-screen bg-navy-950 font-sans text-slate-100 overflow-x-hidden selection:bg-blue-500/30">
      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center pt-20 pb-32 px-6 overflow-hidden">
        {/* Background Decorations */}
        <div className="absolute inset-0 z-0">
          <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[120px] mix-blend-screen" />
          <div className="absolute bottom-1/4 right-1/4 w-[600px] h-[600px] bg-cyan-600/10 rounded-full blur-[150px] mix-blend-screen" />
          <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:64px_64px] [mask-image:radial-gradient(ellipse_60%_60%_at_50%_50%,#000_70%,transparent_100%)]" />
        </div>

        <div className="relative z-10 flex flex-col items-center text-center max-w-5xl mx-auto">
          <img src={logoImg} alt='AERO RECON-3D' className='h-16 md:h-20 w-auto mb-8' />
          
          <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold text-white leading-tight max-w-4xl tracking-tight">
            Transform Drone Video into <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-400">Accurate 3D Reality</span>
          </h1>
          
          <p className="text-base md:text-lg text-slate-400 max-w-2xl mt-6 leading-relaxed">
            Generate georeferenced, metrically accurate 3D models from single-pass UAV video using AI-powered computer vision, camera pose estimation, depth reconstruction and spatial data fusion.
          </p>
          
          <div className="flex gap-4 mt-8 flex-wrap justify-center">
            <Link 
              to="/reconstruction/new" 
              className="bg-blue-600 hover:bg-blue-500 text-white px-8 py-3.5 rounded-lg font-semibold text-lg transition-all shadow-lg shadow-blue-600/25 flex items-center gap-2 group"
            >
              <Rocket className="w-5 h-5 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
              Start Reconstruction
            </Link>
            <Link 
              to="/dashboard" 
              className="border border-blue-500/50 text-blue-400 hover:bg-blue-500/10 hover:border-blue-400 px-8 py-3.5 rounded-lg font-semibold text-lg transition-all flex items-center gap-2"
            >
              <Play className="w-5 h-5" />
              Explore Demo
            </Link>
          </div>
          
          <p className="text-slate-500 text-sm mt-8 font-medium tracking-wide">
            Problem Statement ID: 26158 &bull; SIH 2026
          </p>
        </div>
      </section>

      {/* Pipeline Section */}
      <section className="py-20 lg:py-28 bg-navy-900 relative border-y border-navy-800">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-2xl md:text-3xl font-bold text-center mb-4 text-white">How It Works</h2>
          <p className="text-slate-400 text-center mb-16 max-w-2xl mx-auto">From raw drone footage to validated 3D reconstruction</p>
          
          <div className="relative">
            {/* Desktop Connecting Line */}
            <div className="hidden md:block absolute top-[4.5rem] left-0 right-0 h-0.5 bg-gradient-to-r from-blue-500/30 via-cyan-500/30 to-blue-500/30 z-0" />
            
            <div className="grid grid-cols-1 md:grid-cols-4 lg:grid-cols-8 gap-8 relative z-10">
              {steps.map((step, idx) => (
                <div key={idx} className="flex flex-row md:flex-col items-center md:text-center gap-4 md:gap-0">
                  <div className="md:hidden w-0.5 h-full absolute left-8 -ml-px bg-gradient-to-b from-blue-500/30 to-cyan-500/30 -z-10" />
                  
                  <div className="w-8 h-8 rounded-full bg-blue-600/20 text-blue-400 text-sm font-bold flex flex-shrink-0 items-center justify-center md:mb-4 ring-4 ring-navy-900">
                    {idx + 1}
                  </div>
                  
                  <div className="bg-navy-800 border border-navy-600/50 rounded-xl p-4 md:mb-3 shadow-lg shadow-black/20 group hover:border-blue-500/50 transition-colors flex-shrink-0">
                    <step.icon className="w-6 h-6 text-slate-300 group-hover:text-cyan-400 transition-colors" />
                  </div>
                  
                  <div>
                    <h3 className="text-sm font-semibold text-slate-200">{step.name}</h3>
                    <p className="text-xs text-slate-500 mt-1 hidden md:block">{step.desc}</p>
                    <p className="text-sm text-slate-500 mt-1 md:hidden">{step.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Why Section */}
      <section className="py-20 lg:py-28 bg-navy-950 relative">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-2xl md:text-3xl font-bold text-center mb-16 text-white">Why AERO RECON-3D</h2>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {whyCards.map((card, idx) => (
              <div key={idx} className="bg-navy-800/80 border border-navy-600/50 rounded-xl p-6 hover:-translate-y-1 hover:border-blue-500/30 transition-all duration-300 group shadow-lg shadow-black/10">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500/20 to-cyan-500/20 rounded-lg flex items-center justify-center mb-4 group-hover:from-blue-500/30 transition-colors">
                  <card.icon className="w-6 h-6 text-blue-400" />
                </div>
                <h3 className="font-semibold text-lg mb-2 text-slate-200">{card.title}</h3>
                <p className="text-sm text-slate-400 leading-relaxed">{card.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Use Cases Section */}
      <section className="py-20 lg:py-28 bg-navy-900 border-t border-navy-800">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-2xl md:text-3xl font-bold text-center mb-16 text-white">Applications</h2>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-5">
            {useCases.map((useCase, idx) => (
              <div key={idx} className="bg-navy-800 border border-navy-600/50 rounded-xl p-5 text-center hover:border-blue-500/30 transition-all hover:shadow-xl hover:shadow-black/20 group">
                <div className="w-10 h-10 mx-auto bg-navy-900 rounded-full flex items-center justify-center mb-3 group-hover:scale-110 transition-transform border border-navy-700 group-hover:border-blue-500/30">
                  <useCase.icon className="w-5 h-5 text-cyan-400" />
                </div>
                <h3 className="font-semibold text-base mb-2 text-slate-200">{useCase.title}</h3>
                <p className="text-xs text-slate-400">{useCase.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-navy-950 border-t border-navy-600/20 pt-16 pb-6 px-6">
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-10 mb-12">
          {/* Col 1 */}
          <div className="flex flex-col items-start">
            <img src={logoImg} alt='AERO RECON-3D' className='h-8 w-auto mb-4' />
            <p className="text-sm text-slate-500 max-w-xs">
              Transforming raw drone footage into highly accurate, validated 3D reality models using advanced AI and computer vision.
            </p>
          </div>
          
          {/* Col 2 */}
          <div className="flex flex-col md:items-center">
            <div>
              <h4 className="text-white font-semibold mb-4">Navigation</h4>
              <ul className="space-y-2">
                <li><Link to="/dashboard" className="text-sm text-slate-400 hover:text-slate-200 transition-colors">Dashboard</Link></li>
                <li><Link to="/projects" className="text-sm text-slate-400 hover:text-slate-200 transition-colors">Projects</Link></li>
                <li><Link to="/docs" className="text-sm text-slate-400 hover:text-slate-200 transition-colors">Documentation</Link></li>
              </ul>
            </div>
          </div>
          
          {/* Col 3 */}
          <div className="flex flex-col md:items-end text-left md:text-right">
            <div>
              <h4 className="text-white font-semibold mb-4">Hackathon Info</h4>
              <ul className="space-y-2 text-sm text-slate-400">
                <li>Problem Statement: <span className="text-slate-300">26158</span></li>
                <li>Theme: <span className="text-slate-300">Robotics & Drones</span></li>
                <li>Category: <span className="text-slate-300">Software</span></li>
              </ul>
            </div>
          </div>
        </div>
        
        <div className="max-w-7xl mx-auto border-t border-navy-600/20 pt-6 text-center">
          <p className="text-xs text-slate-600">
            &copy; 2026 AERO RECON-3D — Smart India Hackathon
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
