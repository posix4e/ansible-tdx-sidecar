import { useParams, Link } from 'react-router-dom';
import { useRegistration, useCaptureBaseline } from '../hooks/useRegistrations';
import { useVerifyRegistration, useVerificationHistory } from '../hooks/useVerification';
import { StatusBadge } from '../components/StatusBadge';
import { MeasurementsDisplay } from '../components/MeasurementsDisplay';
import { VerificationStatus } from '../components/VerificationStatus';

export function ApplicationDetails() {
  const { id } = useParams<{ id: string }>();
  const { data: app, isLoading, refetch } = useRegistration(id!);
  const { data: history } = useVerificationHistory(id);
  const verifyMutation = useVerifyRegistration();
  const baselineMutation = useCaptureBaseline();

  const handleVerify = async () => {
    if (id) {
      await verifyMutation.mutateAsync({ registrationId: id });
      refetch();
    }
  };

  const handleCaptureBaseline = async () => {
    if (id) {
      await baselineMutation.mutateAsync(id);
      refetch();
    }
  };

  if (isLoading) return <div className="text-center py-12">Loading...</div>;
  if (!app) return <div className="text-center py-12">Application not found</div>;

  const hasBaseline = !!app.expected_mrtd;
  const latestVerification = history?.[0];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="mb-6">
        <Link to="/" className="text-tdx-primary hover:underline">&larr; Back to Dashboard</Link>
      </div>

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold">{app.name}</h1>
          <p className="text-gray-600">{app.description}</p>
        </div>
        <StatusBadge status={hasBaseline ? 'verified' : 'unverified'} size="lg" />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border">
          <div className="text-xs text-gray-500">GitHub</div>
          <div className="font-medium truncate">{app.github_org}/{app.github_repo}</div>
        </div>
        <div className="bg-white p-4 rounded-lg border">
          <div className="text-xs text-gray-500">Image</div>
          <div className="font-medium truncate" title={app.image_repository}>{app.image_repository}:{app.image_tag}</div>
        </div>
        <div className="bg-white p-4 rounded-lg border">
          <div className="text-xs text-gray-500">App Endpoint</div>
          <div className="font-mono text-sm truncate">{app.app_endpoint}</div>
        </div>
        <div className="bg-white p-4 rounded-lg border">
          <div className="text-xs text-gray-500">TDX Proxy</div>
          <div className="font-mono text-sm truncate">{app.tdx_proxy_endpoint}</div>
        </div>
      </div>

      {app.proxy_url && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="text-sm text-blue-700 font-medium">Proxy URL</div>
          <code className="text-blue-900">{app.proxy_url}</code>
          <p className="text-xs text-blue-600 mt-1">Use this URL to access the application through the attestation-verified proxy</p>
        </div>
      )}

      <div className="flex gap-4">
        <button
          onClick={handleCaptureBaseline}
          disabled={baselineMutation.isPending}
          className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50"
        >
          {baselineMutation.isPending ? 'Capturing...' : 'Capture Baseline'}
        </button>
        <button
          onClick={handleVerify}
          disabled={verifyMutation.isPending}
          className="px-4 py-2 bg-tdx-primary text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {verifyMutation.isPending ? 'Verifying...' : 'Verify Now'}
        </button>
      </div>

      {hasBaseline && (
        <div className="bg-white p-6 rounded-lg border">
          <h2 className="text-lg font-semibold mb-4">Expected Measurements (Baseline)</h2>
          <MeasurementsDisplay
            measurements={{
              mrtd: app.expected_mrtd || '',
              rtmr0: app.expected_rtmr0 || '',
              rtmr1: app.expected_rtmr1 || '',
              rtmr2: app.expected_rtmr2 || '',
              rtmr3: app.expected_rtmr3 || '',
            }}
            showCopyButtons
          />
        </div>
      )}

      {latestVerification && (
        <div className="bg-white p-6 rounded-lg border">
          <h2 className="text-lg font-semibold mb-4">Latest Verification</h2>
          <VerificationStatus result={latestVerification} onRerun={handleVerify} />
        </div>
      )}

      {history && history.length > 1 && (
        <div className="bg-white p-6 rounded-lg border">
          <h2 className="text-lg font-semibold mb-4">Verification History</h2>
          <div className="space-y-2">
            {history.slice(1, 6).map((v) => (
              <div key={v.id} className="flex items-center justify-between py-2 border-b last:border-0">
                <StatusBadge status={v.status} size="sm" />
                <span className="text-sm text-gray-500">{new Date(v.created_at).toLocaleString()}</span>
                <span className="text-sm text-gray-500">{v.verification_duration_ms}ms</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
