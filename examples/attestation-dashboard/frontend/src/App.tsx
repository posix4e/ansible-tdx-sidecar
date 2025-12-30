import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Dashboard } from './pages/Dashboard';
import { Register } from './pages/Register';
import { ApplicationDetails } from './pages/ApplicationDetails';

export function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white border-b">
          <div className="max-w-6xl mx-auto px-4 py-4">
            <div className="flex items-center gap-3">
              <svg className="w-8 h-8 text-tdx-primary" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
              </svg>
              <span className="text-xl font-bold text-gray-900">TDX Attestation</span>
            </div>
          </div>
        </header>

        <main className="px-4 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/register" element={<Register />} />
            <Route path="/applications/:id" element={<ApplicationDetails />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
