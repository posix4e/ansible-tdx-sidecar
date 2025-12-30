import { useState } from 'react';
import type { VerificationResponse } from '../types';
import { StatusBadge } from './StatusBadge';
import { MeasurementsDisplay } from './MeasurementsDisplay';

interface VerificationStatusProps {
  result: VerificationResponse;
  onRerun?: () => void;
}

function ExpandableSection({
  title,
  verified,
  error,
  children,
}: {
  title: string;
  verified: boolean;
  error?: string | null;
  children: React.ReactNode;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border rounded-lg overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100"
      >
        <div className="flex items-center gap-3">
          <span className={`w-3 h-3 rounded-full ${verified ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="font-medium">{title}</span>
        </div>
        <svg
          className={`w-5 h-5 transition-transform ${expanded ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {expanded && (
        <div className="p-4 border-t">
          {error && <p className="text-red-600 text-sm mb-3">{error}</p>}
          {children}
        </div>
      )}
    </div>
  );
}

export function VerificationStatus({ result, onRerun }: VerificationStatusProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <StatusBadge status={result.status} size="lg" />
          <span className="text-gray-500">
            Verified in {result.verification_duration_ms}ms
          </span>
        </div>
        {onRerun && (
          <button
            onClick={onRerun}
            className="px-4 py-2 bg-tdx-primary text-white rounded-lg hover:bg-blue-700"
          >
            Re-verify
          </button>
        )}
      </div>

      <ExpandableSection
        title="DCAP Quote Verification"
        verified={result.dcap.verified}
        error={result.dcap.error}
      >
        <dl className="grid grid-cols-2 gap-2 text-sm">
          <dt className="text-gray-500">Status:</dt>
          <dd className="font-mono">{result.dcap.status}</dd>
          {result.dcap.tcb_status && (
            <>
              <dt className="text-gray-500">TCB Status:</dt>
              <dd className="font-mono">{result.dcap.tcb_status}</dd>
            </>
          )}
        </dl>
      </ExpandableSection>

      <ExpandableSection
        title="GitHub Attestation"
        verified={result.github.verified}
        error={result.github.error}
      >
        <dl className="grid grid-cols-2 gap-2 text-sm">
          {result.github.repository && (
            <>
              <dt className="text-gray-500">Repository:</dt>
              <dd className="font-mono">{result.github.repository}</dd>
            </>
          )}
          {result.github.workflow_ref && (
            <>
              <dt className="text-gray-500">Workflow:</dt>
              <dd className="font-mono truncate">{result.github.workflow_ref}</dd>
            </>
          )}
          {result.github.build_trigger && (
            <>
              <dt className="text-gray-500">Trigger:</dt>
              <dd className="font-mono">{result.github.build_trigger}</dd>
            </>
          )}
        </dl>
      </ExpandableSection>

      <ExpandableSection
        title="TDX Measurements"
        verified={result.measurements.verified}
        error={result.measurements.error}
      >
        {result.measurements.actual_measurements ? (
          <MeasurementsDisplay
            measurements={result.measurements.actual_measurements}
            expected={result.measurements.expected_measurements}
            showCopyButtons
          />
        ) : (
          <p className="text-gray-500">No measurements available</p>
        )}
      </ExpandableSection>
    </div>
  );
}
