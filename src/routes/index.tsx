import { createHashRouter, Navigate } from 'react-router-dom';
import { AppLayout } from '../layouts/AppLayout';

import Dashboard from '../pages/Dashboard';
import Projects from '../pages/Projects';
import ProjectDetails from '../pages/ProjectDetails';
import NewReconstruction from '../pages/NewReconstruction';
import Processing from '../pages/Processing';
import Viewer from '../pages/Viewer';
import Accuracy from '../pages/Accuracy';
import Reports from '../pages/Reports';
import Settings from '../pages/Settings';

export const router = createHashRouter([
  // ── Redirect Root to Dashboard ──
  {
    path: '/',
    element: <Navigate to='/dashboard' replace />,
  },

  // ── Application Routes (inside AppLayout with sidebar/header) ──
  {
    element: <AppLayout />,
    children: [
      {
        path: '/dashboard',
        element: <Dashboard />,
      },
      {
        path: '/projects',
        element: <Projects />,
      },
      {
        path: '/projects/:id',
        element: <ProjectDetails />,
      },
      {
        path: '/reconstruction/new',
        element: <NewReconstruction />,
      },
      {
        path: '/processing',
        element: <Processing />,
      },
      {
        path: '/viewer',
        element: <Viewer />,
      },
      {
        path: '/accuracy/:id?',
        element: <Accuracy />,
      },
      {
        path: '/reports',
        element: <Reports />,
      },
      {
        path: '/settings',
        element: <Settings />,
      },
    ],
  },

  // ── Fallback ──
  {
    path: '*',
    element: <Navigate to="/dashboard" replace />,
  },
]);
