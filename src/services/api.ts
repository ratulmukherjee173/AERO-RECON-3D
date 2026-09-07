// ============================================================
// AERO RECON-3D — API Service Stubs
// These are placeholder abstractions for Phase 2 backend integration
// ============================================================

import type { ApiResponse, Project, ProjectDetails, Report } from '../types';
import { mockProjects, mockProjectDetails, mockReports, mockProcessingStages, mockProcessingMetrics, mockAccuracyMetrics } from '../data/mock';

const API_BASE = '/api';

// Placeholder — simulates async API call with mock data
function simulateDelay<T>(data: T, ms = 300): Promise<ApiResponse<T>> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ data, success: true });
    }, ms);
  });
}

// ── Projects API ──
export const projectsApi = {
  getAll: () => simulateDelay<Project[]>(mockProjects),
  getById: (id: string) =>
    simulateDelay<ProjectDetails | null>(mockProjectDetails[id] ?? null),
  create: (_data: Partial<Project>) =>
    simulateDelay<Project>({ ...mockProjects[0], id: 'new-' + Date.now() }),
  delete: (_id: string) => simulateDelay<boolean>(true),
};

// ── Reconstruction API ──
export const reconstructionApi = {
  start: (_projectId: string, _config: unknown) =>
    simulateDelay({ jobId: 'job-' + Date.now(), status: 'started' }),
  getStatus: (_jobId: string) =>
    simulateDelay({ progress: 72, stage: 'Point Cloud Generation' }),
  cancel: (_jobId: string) => simulateDelay({ cancelled: true }),
};

// ── Processing API ──
export const processingApi = {
  getStages: (_projectId: string) =>
    simulateDelay(mockProcessingStages),
  getMetrics: (_projectId: string) =>
    simulateDelay(mockProcessingMetrics),
};

// ── Models API ──
export const modelsApi = {
  getViewer: (_modelId: string) =>
    simulateDelay({ modelUrl: '', layers: [], info: {} }),
  exportModel: (_modelId: string, _format: string) =>
    simulateDelay({ downloadUrl: '#' }),
};

// ── Accuracy API ──
export const accuracyApi = {
  getMetrics: (_projectId: string) =>
    simulateDelay(mockAccuracyMetrics),
};

// ── Upload API ──
export const uploadApi = {
  upload: (_file: File, _onProgress: (p: number) => void) =>
    simulateDelay({ fileId: 'file-' + Date.now(), status: 'completed' }, 1000),
};

// ── Reports API ──
export const reportsApi = {
  getAll: () => simulateDelay<Report[]>(mockReports),
  generate: (_projectId: string) =>
    simulateDelay({ reportId: 'rpt-' + Date.now(), status: 'generating' }),
  download: (_reportId: string) =>
    simulateDelay({ downloadUrl: '#' }),
};

export { API_BASE };
