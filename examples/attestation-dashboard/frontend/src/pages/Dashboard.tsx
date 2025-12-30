import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useRegistrations, useDeleteRegistration } from '../hooks/useRegistrations';
import { useSystemStatus } from '../hooks/useVerification';
import { RegistrationCard } from '../components/RegistrationCard';

export function Dashboard() {
  const { data: registrations, isLoading, error, refetch } = useRegistrations();
  const { data: status } = useSystemStatus();
  const deleteRegistration = useDeleteRegistration();
  const [filter, setFilter] = useState<'all' | 'verified' | 'unverified'>('all');

  const filteredRegistrations = registrations?.filter((r) => {
    if (filter === 'all') return true;
    if (filter === 'verified') return !!r.expected_mrtd;
    if (filter === 'unverified') return !r.expected_mrtd;
    return true;
  });

  const handleDelete = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this registration?')) {
      await deleteRegistration.mutateAsync(id);
    }
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">TDX Attestation Dashboard</h1>
          <p className="text-gray-600 mt-1">Manage and verify TDX-attested applications</p>
        </div>
        <Link
          to="/register"
          className="px-4 py-2 bg-tdx-primary text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Register Application
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-white p-4 rounded-lg border">
          <div className="text-sm text-gray-500">TDX Available</div>
          <div className="flex items-center gap-2 mt-1">
            <span className={`w-3 h-3 rounded-full ${status?.tdx_available ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="font-medium">{status?.tdx_available ? 'Yes' : 'No'}</span>
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg border">
          <div className="text-sm text-gray-500">DCAP Library</div>
          <div className="flex items-center gap-2 mt-1">
            <span className={`w-3 h-3 rounded-full ${status?.dcap_library_available ? 'bg-green-500' : 'bg-yellow-500'}`} />
            <span className="font-medium">{status?.dcap_library_available ? 'Available' : 'Mock Mode'}</span>
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg border">
          <div className="text-sm text-gray-500">Registered Apps</div>
          <div className="text-2xl font-bold mt-1">{registrations?.length ?? 0}</div>
        </div>
      </div>

      <div className="flex items-center gap-4 mb-6">
        <span className="text-gray-500">Filter:</span>
        <div className="flex gap-2">
          {(['all', 'verified', 'unverified'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1 rounded-full text-sm ${
                filter === f ? 'bg-tdx-primary text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
        <button onClick={() => refetch()} className="ml-auto text-gray-500 hover:text-gray-700" title="Refresh">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-gray-500">Loading...</div>
      ) : error ? (
        <div className="text-center py-12 text-red-600">Error loading registrations</div>
      ) : filteredRegistrations?.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed">
          <h3 className="mt-4 text-lg font-medium text-gray-900">No applications registered</h3>
          <p className="mt-1 text-gray-500">Get started by registering a TDX application.</p>
          <Link to="/register" className="mt-4 inline-block px-4 py-2 bg-tdx-primary text-white rounded-lg hover:bg-blue-700">
            Register Application
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredRegistrations?.map((registration) => (
            <RegistrationCard key={registration.id} registration={registration} onDelete={() => handleDelete(registration.id)} />
          ))}
        </div>
      )}
    </div>
  );
}
