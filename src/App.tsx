import { RouterProvider } from 'react-router-dom';
import { router } from './routes';
import { SettingsProvider } from './contexts/SettingsContext';


export default function App() {
  return (
    <SettingsProvider>
      <RouterProvider router={router} />
    </SettingsProvider>
  );
}
