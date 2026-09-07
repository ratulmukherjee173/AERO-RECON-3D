// ============================================================
// AERO RECON-3D — TypeScript Type Definitions
// ============================================================

export type ProjectStatus = 'completed' | 'processing' | 'failed' | 'pending';
export type ProcessingStageStatus = 'completed' | 'processing' | 'pending';
export type ProcessingQuality = 'preview' | 'standard' | 'high';
export type ReportStatus = 'ready' | 'generating' | 'failed';

export interface Project {
  id: string;
  name: string;
  location: string;
  date: string;
  status: ProjectStatus;
  progress: number;
  accuracy: number;
  thumbnail?: string;
  description?: string;
  isDemo?: boolean;
}

export interface ProjectDetails extends Project {
  flightDate: string;
  flightDuration: string;
  videoResolution: string;
  gpsAvailable: boolean;
  imuAvailable: boolean;
  totalFrames: number;
  cameraPoses: number;
  pointCloudPoints: string;
  modelSize: string;
  processingTime: string;
  area: string;
  altitude: string;
}

export interface ProcessingStage {
  id: number;
  name: string;
  status: ProcessingStageStatus;
  progress?: number;
  duration?: string;
}

export interface ProcessingMetrics {
  framesProcessed: number;
  totalFrames: number;
  featurePoints: number;
  cameraPoses: number;
  depthMaps: number;
  pointCloudPoints: string;
}

export interface ResourceUsage {
  cpu: number;
  gpu: number;
  memory: number;
}

export interface AccuracyMetrics {
  horizontalError: number;
  verticalError: number;
  scaleError: number;
  reconstructionConfidence: number;
  rmse: number;
  mae: number;
  maxDeviation: number;
  alignmentError: number;
}

export interface ViewerLayer {
  id: string;
  name: string;
  icon: string;
  visible: boolean;
  color: string;
}

export interface Measurement {
  id: string;
  type: 'distance' | 'area' | 'height';
  value: number;
  unit: string;
}

export interface Report {
  id: string;
  projectName: string;
  generatedDate: string;
  accuracy: number;
  status: ReportStatus;
  type: string;
}

export interface DashboardStats {
  totalProjects: number;
  completedReconstructions: number;
  modelsGenerated: number;
  avgConfidence: number;
}

export interface Notification {
  id: string;
  title: string;
  message: string;
  time: string;
  read: boolean;
  type: 'info' | 'success' | 'warning' | 'error';
}

export interface UserProfile {
  name: string;
  email: string;
  avatar?: string;
  role: string;
}

export interface UploadFile {
  name: string;
  size: string;
  duration: string;
  resolution: string;
  progress: number;
  status: 'uploading' | 'completed' | 'error';
}

export interface FlightData {
  gpsData: boolean;
  imuData: boolean;
  cameraIntrinsics: string;
  flightAltitude: string;
  rtkPpk: boolean;
}

export interface ReconstructionConfig {
  quality: ProcessingQuality;
  outputs: {
    pointCloud: boolean;
    texturedMesh: boolean;
    dsm: boolean;
    orthoMap: boolean;
  };
}

export interface ErrorDistributionPoint {
  range: string;
  count: number;
}

export interface CoverageSector {
  name: string;
  value: number;
  color: string;
}

// API Service types (placeholders for Phase 2)
export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
}
