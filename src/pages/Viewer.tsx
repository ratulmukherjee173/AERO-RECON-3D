import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Center, useProgress, Html } from '@react-three/drei';
import * as THREE from 'three';
import { PLYLoader } from 'three/examples/jsm/loaders/PLYLoader.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { 
  RotateCw, Move, ZoomIn, Maximize2, Layers as LayersIcon, 
  Info, Ruler, Square, ArrowUpDown, Eye, EyeOff, Download,
  AlertTriangle, Box
} from 'lucide-react';
import { mockViewerLayers } from '../data/mock';
import { apiFetch, BACKEND_URL } from '../utils/api';
import { safeGetStorage } from '../utils/storage';

function Loader() {
  const { progress } = useProgress();
  return (
    <Html center>
      <div className="flex flex-col items-center gap-3 bg-navy-950/90 backdrop-blur-md px-6 py-4 rounded-xl border border-navy-700 shadow-[0_0_20px_rgba(34,211,238,0.1)] whitespace-nowrap">
        <div className="w-8 h-8 border-4 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin" />
        <div className="text-slate-200 font-bold tracking-wide uppercase text-sm">Loading 3D Model</div>
        {progress > 0 && <div className="text-cyan-400 text-xs font-bold tracking-widest">{progress.toFixed(0)}% DOWNLOADED</div>}
        <div className="text-[10px] text-slate-500 mt-1 max-w-[200px] text-center whitespace-normal font-medium leading-relaxed uppercase tracking-widest">
          Parsing may take several seconds for large files. Browser may pause.
        </div>
      </div>
    </Html>
  );
}

function ModelViewer({ 
  jobId,
  activeLayer,
  pointSize, 
  onLoaded, 
  onError 
}: { 
  jobId: string, 
  activeLayer: string,
  pointSize: number,
  onLoaded: (count: number) => void,
  onError: () => void
}) {
  const [model, setModel] = useState<THREE.Object3D | null>(null);
  const [geometry, setGeometry] = useState<THREE.BufferGeometry | null>(null);

  useEffect(() => {
    let currentGeo: THREE.BufferGeometry | null = null;
    let currentModel: THREE.Object3D | null = null;
    let isMounted = true;
    const abortController = new AbortController();

    const cleanup = () => {
      if (currentGeo) {
        currentGeo.dispose();
      }
      if (currentModel) {
        currentModel.traverse((child) => {
          if (child instanceof THREE.Mesh) {
            child.geometry?.dispose();
            if (Array.isArray(child.material)) {
              child.material.forEach(m => {
                m.map?.dispose();
                m.dispose();
              });
            } else if (child.material) {
              child.material.map?.dispose();
              child.material.dispose();
            }
          }
        });
      }
      currentGeo = null;
      currentModel = null;
      if (isMounted) {
        setGeometry(null);
        setModel(null);
      }
    };

    cleanup();

    const loadPLY = () => {
      apiFetch(`/download/${jobId}/preview`, { signal: abortController.signal })
        .then(res => {
          if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
          return res.arrayBuffer();
        })
        .then(buffer => {
          if (!isMounted) return;
          const loader = new PLYLoader();
          const geo = loader.parse(buffer);
          currentGeo = geo;
          setGeometry(geo);
          onLoaded(geo.attributes.position.count);
        })
        .catch(err => {
          if (err.name === 'AbortError') return;
          if (!isMounted) return;
          console.error('Failed to load PLY:', err);
          onError();
        });
    };

    const loadGLB = () => {
      apiFetch(`/download/${jobId}/glb`, { signal: abortController.signal })
        .then(res => {
          if (!res.ok) throw new Error("No GLB");
          return res.arrayBuffer();
        })
        .then(buffer => {
          if (!isMounted) return;
          const loader = new GLTFLoader();
          loader.parse(buffer, '', (gltf) => {
            if (!isMounted) return;
            
            let vertexCount = 0;
            let triangleCount = 0;
            let isValid = true;
            
            gltf.scene.traverse((child) => {
              if (child instanceof THREE.Mesh && child.geometry && child.geometry.attributes.position) {
                const pos = child.geometry.attributes.position;
                vertexCount += pos.count;
                if (child.geometry.index) {
                   triangleCount += child.geometry.index.count / 3;
                } else {
                   triangleCount += pos.count / 3;
                }
                
                const array = pos.array;
                for (let i = 0; i < Math.min(100, array.length); i++) {
                   if (Number.isNaN(array[i])) isValid = false;
                }
                
                if (child.material && child.geometry.hasAttribute('color')) {
                  child.material.vertexColors = true;
                  child.material.needsUpdate = true;
                }
              }
            });
            
            // Safe Browser Preview Budget
            if (!isValid || triangleCount > 150000 || vertexCount > 200000) {
               console.warn(`Model too large or invalid. Vertices: ${vertexCount}, Triangles: ${triangleCount}. Freeing memory & falling back to PLY.`);
               gltf.scene.traverse((child) => {
                 if (child instanceof THREE.Mesh) {
                   child.geometry?.dispose();
                   if (child.material) child.material.dispose();
                 }
               });
               loadPLY();
               return;
            }
            
            currentModel = gltf.scene;
            setModel(gltf.scene);
            onLoaded(vertexCount);
          }, (err) => {
            console.error('GLTF parse error:', err);
            loadPLY();
          });
        })
        .catch(err => {
          if (err.name === 'AbortError') return;
          if (!isMounted) return;
          console.error('GLB fetch error:', err);
          loadPLY();
        });
    };

    if (activeLayer === 'mesh') {
      loadGLB();
    } else if (activeLayer === 'pointcloud') {
      loadPLY();
    } else {
      // Just clear
      onLoaded(0);
    }

    return () => {
      isMounted = false;
      abortController.abort();
      cleanup();
    };
  }, [jobId, activeLayer, onLoaded, onError]);

  if (!geometry && !model && activeLayer !== 'none') return <Loader />;

  if (model && activeLayer === 'mesh') {
    return (
      <Center>
        <primitive object={model} />
      </Center>
    );
  }

  if (geometry && activeLayer === 'pointcloud') {
    return (
      <Center>
        <points>
          <primitive object={geometry} attach="geometry" />
          <pointsMaterial 
            size={pointSize} 
            vertexColors={geometry.hasAttribute('color')} 
            color={geometry.hasAttribute('color') ? undefined : 0x88ccff} 
            sizeAttenuation={true} 
          />
        </points>
      </Center>
    );
  }

  return null;
}

export default function Viewer() {
  const [searchParams] = useSearchParams();
  const jobId = searchParams.get('jobId') || safeGetStorage('last_job_id');

  const [activeTool, setActiveTool] = useState('rotate');
  const [activeMeasure, setActiveMeasure] = useState<string | null>(null);
  const [showLeftPanel, setShowLeftPanel] = useState(true);
  const [showRightPanel, setShowRightPanel] = useState(true);
  const [layers, setLayers] = useState(mockViewerLayers);
  
  const [pointCount, setPointCount] = useState<number | null>(null);
  const [hasError, setHasError] = useState(false);
  const [pointSize, setPointSize] = useState(0.05);

  const [hasContextLost, setHasContextLost] = useState(false);

  const controlsRef = useRef<any>(null);

  const toggleLayer = (id: string) => {
    // Only one layer can be visible at a time
    setLayers(layers.map(l => ({ ...l, visible: l.id === id })));
  };

  const activeLayerId = layers.find(l => l.visible)?.id || 'none';

  const resetView = () => {
    if (controlsRef.current) {
      controlsRef.current.reset();
    }
  };

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
    } else {
      document.exitFullscreen().catch(() => {});
    }
  };

  if (!jobId) {
    return (
      <div className="h-[calc(100vh-theme(spacing.16))] flex flex-col items-center justify-center text-center px-4 bg-[#050A15] -m-4 sm:-m-6 lg:-m-8">
        <Box className="w-16 h-16 text-slate-600 mb-4" />
        <h2 className="text-2xl font-bold text-slate-200 mb-2 tracking-tight">No 3D Models Available</h2>
        <p className="text-slate-400 max-w-md text-sm leading-relaxed">
          You haven't processed any reconstruction jobs yet. 
          Upload a video to generate your first 3D model.
        </p>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-theme(spacing.16))] relative overflow-hidden -m-4 sm:-m-6 lg:-m-8 bg-[#050A15]">
      
      {/* 3D Canvas Area */}
      <div className="absolute inset-0">
        {hasContextLost ? (
          <div className="w-full h-full flex flex-col items-center justify-center p-6 text-center">
            <AlertTriangle className="w-12 h-12 text-amber-500/50 mb-4" />
            <h2 className="text-xl font-bold tracking-tight text-slate-200">WebGL Context Lost</h2>
            <p className="text-slate-400 mt-2 max-w-md mb-6 text-sm">
              The graphics memory limit was exceeded. The preview has been stopped to prevent your browser from freezing.
            </p>
            <button 
              onClick={() => window.location.reload()}
              className="px-6 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs font-bold tracking-widest uppercase transition-all shadow-[0_0_15px_rgba(8,145,178,0.4)]"
            >
              Reload Viewer
            </button>
          </div>
        ) : !hasError ? (
          <Canvas 
            camera={{ position: [0, 0, 10], fov: 50 }}
            onCreated={({ gl }) => {
              gl.domElement.addEventListener('webglcontextlost', (e) => {
                e.preventDefault();
                setHasContextLost(true);
              });
            }}
          >
            <color attach="background" args={['#050a15']} />
            <ambientLight intensity={0.5} />
            <directionalLight position={[10, 10, 10]} intensity={1} />
            
            <ModelViewer 
              jobId={jobId} 
              activeLayer={activeLayerId}
              pointSize={pointSize}
              onLoaded={setPointCount}
              onError={() => setHasError(true)}
            />
            
            <OrbitControls 
              ref={controlsRef}
              makeDefault
              enablePan={activeTool === 'pan' || activeTool === 'rotate'}
              enableZoom={activeTool === 'zoom' || activeTool === 'rotate'}
              enableRotate={activeTool === 'rotate'}
            />
          </Canvas>
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center p-6 text-center">
            <AlertTriangle className="w-12 h-12 text-red-500/50 mb-4" />
            <h2 className="text-xl font-bold tracking-tight text-slate-200">Failed to Load Model</h2>
            <p className="text-slate-400 mt-2 max-w-md text-sm">
              The 3D model is not available for this reconstruction job ({jobId}). It may still be processing, or the file was not generated successfully.
            </p>
          </div>
        )}
      </div>

      {/* Top Toolbar */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-20 flex gap-2">
        <div className="bg-[#0A1224]/90 backdrop-blur-md rounded-xl border border-navy-700/80 p-1.5 flex items-center gap-1 shadow-[0_0_20px_rgba(5,10,21,0.5)]">
          <button className="p-2 rounded-lg hover:bg-navy-800 text-slate-300 md:hidden transition-colors" onClick={() => setShowLeftPanel(!showLeftPanel)}><LayersIcon size={18} /></button>
          
          <div className="w-px h-6 bg-navy-700 mx-1 md:hidden" />
          
          <button onClick={() => setActiveTool('rotate')} className={`p-2 rounded-lg transition-all ${activeTool === 'rotate' ? 'bg-cyan-500/20 text-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.2)]' : 'text-slate-400 hover:bg-navy-800 hover:text-slate-200'}`} title="Rotate"><RotateCw size={18} /></button>
          <button onClick={() => setActiveTool('pan')} className={`p-2 rounded-lg transition-all ${activeTool === 'pan' ? 'bg-cyan-500/20 text-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.2)]' : 'text-slate-400 hover:bg-navy-800 hover:text-slate-200'}`} title="Pan"><Move size={18} /></button>
          <button onClick={() => setActiveTool('zoom')} className={`p-2 rounded-lg transition-all ${activeTool === 'zoom' ? 'bg-cyan-500/20 text-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.2)]' : 'text-slate-400 hover:bg-navy-800 hover:text-slate-200'}`} title="Zoom"><ZoomIn size={18} /></button>
          
          <div className="w-px h-6 bg-navy-700 mx-1" />
          
          <button onClick={toggleFullscreen} className="p-2 rounded-lg text-slate-400 hover:bg-navy-800 hover:text-slate-200 transition-colors" title="Fullscreen"><Maximize2 size={18} /></button>
          <button onClick={resetView} className="p-2 rounded-lg text-slate-400 hover:bg-navy-800 hover:text-slate-200 transition-colors font-bold text-[10px] uppercase tracking-widest px-3" title="Reset Camera">RESET</button>
          
          <div className="w-px h-6 bg-navy-700 mx-1 md:hidden" />
          <button className="p-2 rounded-lg hover:bg-navy-800 text-slate-300 md:hidden transition-colors" onClick={() => setShowRightPanel(!showRightPanel)}><Info size={18} /></button>
        </div>
      </div>

      {/* Left Panel - Layers */}
      <div className={`absolute left-0 top-0 bottom-0 w-64 bg-[#050A15]/95 backdrop-blur-md border-r border-navy-700 p-6 z-10 transition-transform duration-300 shadow-[10px_0_30px_rgba(0,0,0,0.5)] ${showLeftPanel ? 'translate-x-0' : '-translate-x-full'} hidden md:block`}>
        <h3 className="font-bold text-[10px] uppercase tracking-widest text-cyan-500 mb-6 flex items-center gap-2"><LayersIcon size={14} /> Layers</h3>
        <div className="space-y-1">
          {layers.map(layer => (
            <div key={layer.id} className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-navy-800 transition-colors group">
              <div className="flex items-center gap-3">
                <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: layer.color }} />
                <span className={`text-sm tracking-wide ${layer.visible ? 'text-slate-200 font-semibold' : 'text-slate-500 font-medium'}`}>{layer.name}</span>
              </div>
              <button 
                onClick={() => toggleLayer(layer.id)}
                className={`p-1.5 rounded-md transition-colors ${layer.visible ? 'text-cyan-400 hover:text-cyan-300' : 'text-slate-600 hover:text-slate-400'}`}
              >
                {layer.visible ? <Eye size={16} /> : <EyeOff size={16} />}
              </button>
            </div>
          ))}
        </div>
        
        <div className="mt-8">
           <h3 className="text-[10px] font-bold text-slate-500 mb-4 uppercase tracking-widest">Point Size</h3>
           <input 
             type="range" 
             min="0.01" max="0.5" step="0.01" 
             value={pointSize} 
             onChange={(e) => setPointSize(parseFloat(e.target.value))}
             className="w-full accent-cyan-500"
           />
        </div>
      </div>

      {/* Right Panel - Info */}
      <div className={`absolute right-0 top-0 bottom-0 w-72 bg-[#050A15]/95 backdrop-blur-md border-l border-navy-700 p-6 z-10 transition-transform duration-300 shadow-[-10px_0_30px_rgba(0,0,0,0.5)] ${showRightPanel ? 'translate-x-0' : 'translate-x-full'} hidden md:block`}>
        <h3 className="font-bold text-[10px] uppercase tracking-widest text-cyan-500 mb-6 flex items-center gap-2"><Info size={14} /> Model Information</h3>
        <div className="space-y-5">
          <div>
            <div className="text-[10px] font-bold tracking-widest uppercase text-slate-500 mb-1">Source Job ID</div>
            <div className="text-sm font-semibold text-slate-300 font-mono">{jobId}</div>
          </div>
          <div>
            <div className="text-[10px] font-bold tracking-widest uppercase text-slate-500 mb-1">Vertex Count</div>
            <div className="text-xl font-bold tracking-tight text-slate-200 font-mono">
              {pointCount ? new Intl.NumberFormat().format(pointCount) : 'Loading...'}
            </div>
          </div>
          <div>
            <div className="text-[10px] font-bold tracking-widest uppercase text-slate-500 mb-1">Status</div>
            <div className="text-sm font-bold uppercase tracking-widest flex items-center gap-2">
              {hasError ? (
                <span className="text-red-400">Error</span>
              ) : pointCount ? (
                <span className="text-green-400 drop-shadow-[0_0_5px_rgba(34,197,94,0.5)]">Loaded</span>
              ) : (
                <span className="text-cyan-400">Loading</span>
              )}
            </div>
          </div>
          <div className="pt-4 border-t border-navy-700/50">
            <div className="flex justify-between items-center mb-1.5">
              <span className="text-[10px] font-bold tracking-widest uppercase text-slate-500">Scale</span>
              <span className="text-[10px] font-bold tracking-widest uppercase text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">Relative</span>
            </div>
            <p className="text-[10px] font-medium text-slate-500 mt-2 leading-relaxed">Metric scale and georeferencing not established.</p>
          </div>
        </div>
      </div>

      {/* Bottom Measurement Bar */}
      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-20 flex flex-col items-center gap-3">
        {activeMeasure && (
          <div className="bg-[#0A1224]/90 backdrop-blur-sm border border-cyan-500/30 text-cyan-100 text-[10px] font-bold tracking-widest uppercase px-5 py-2.5 rounded-xl shadow-[0_0_15px_rgba(34,211,238,0.15)] animate-fade-in">
            {activeMeasure === 'distance' && 'Distance: (Requires Metric Scale)'}
            {activeMeasure === 'area' && 'Area: (Requires Metric Scale)'}
            {activeMeasure === 'height' && 'Elevation Δ: (Requires Metric Scale)'}
          </div>
        )}
        <div className="bg-[#0A1224]/90 backdrop-blur-md rounded-xl border border-navy-700/80 p-1.5 flex items-center gap-1 shadow-[0_0_20px_rgba(5,10,21,0.5)]">
          <button onClick={() => setActiveMeasure(activeMeasure === 'distance' ? null : 'distance')} className={`p-2 rounded-lg transition-all ${activeMeasure === 'distance' ? 'bg-cyan-500/20 text-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.2)]' : 'text-slate-400 hover:bg-navy-800 hover:text-slate-200'}`} title="Measure Distance"><Ruler size={18} /></button>
          <button onClick={() => setActiveMeasure(activeMeasure === 'area' ? null : 'area')} className={`p-2 rounded-lg transition-all ${activeMeasure === 'area' ? 'bg-cyan-500/20 text-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.2)]' : 'text-slate-400 hover:bg-navy-800 hover:text-slate-200'}`} title="Measure Area"><Square size={18} /></button>
          <button onClick={() => setActiveMeasure(activeMeasure === 'height' ? null : 'height')} className={`p-2 rounded-lg transition-all ${activeMeasure === 'height' ? 'bg-cyan-500/20 text-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.2)]' : 'text-slate-400 hover:bg-navy-800 hover:text-slate-200'}`} title="Measure Height"><ArrowUpDown size={18} /></button>
        </div>
      </div>

      {/* Bottom-right Actions */}
      <div className="absolute bottom-6 right-6 z-20 flex flex-col gap-2 hidden md:flex">
        <a href={`${BACKEND_URL}/download/${jobId}/ply`} download className="px-5 py-2.5 bg-[#0A1224]/90 hover:bg-navy-800 border border-cyan-500/30 hover:border-cyan-500/50 text-cyan-400 rounded-lg text-[10px] font-bold tracking-widest uppercase transition-all shadow-lg flex items-center gap-2">
          <Download size={14} /> Download PLY
        </a>
      </div>
    </div>
  );
}
