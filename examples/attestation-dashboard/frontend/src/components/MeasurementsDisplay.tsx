import type { TDXMeasurements } from '../types';

interface MeasurementsDisplayProps {
  measurements: TDXMeasurements;
  expected?: TDXMeasurements | null;
  showCopyButtons?: boolean;
}

function CopyButton({ text }: { text: string }) {
  const handleCopy = () => {
    navigator.clipboard.writeText(text);
  };

  return (
    <button
      onClick={handleCopy}
      className="ml-2 text-gray-400 hover:text-gray-600"
      title="Copy to clipboard"
    >
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
        />
      </svg>
    </button>
  );
}

function MeasurementRow({
  label,
  value,
  expectedValue,
  showCopy,
}: {
  label: string;
  value: string;
  expectedValue?: string;
  showCopy?: boolean;
}) {
  const matches = !expectedValue || value.toLowerCase() === expectedValue.toLowerCase();

  return (
    <div className={`p-3 rounded-lg ${matches ? 'bg-gray-50' : 'bg-red-50'}`}>
      <div className="flex items-center justify-between">
        <span className="text-gray-500 uppercase text-xs font-medium">{label}</span>
        {!matches && <span className="text-red-600 text-xs">Mismatch</span>}
      </div>
      <div className="flex items-center mt-1">
        <code className="text-sm font-mono truncate flex-1" title={value}>
          {value || '(not set)'}
        </code>
        {showCopy && value && <CopyButton text={value} />}
      </div>
      {expectedValue && !matches && (
        <div className="mt-1 text-xs text-gray-500">
          Expected: <code className="font-mono">{expectedValue.slice(0, 20)}...</code>
        </div>
      )}
    </div>
  );
}

export function MeasurementsDisplay({
  measurements,
  expected,
  showCopyButtons = false,
}: MeasurementsDisplayProps) {
  const entries: [string, string][] = [
    ['MRTD', measurements.mrtd],
    ['RTMR0', measurements.rtmr0],
    ['RTMR1', measurements.rtmr1],
    ['RTMR2', measurements.rtmr2],
    ['RTMR3', measurements.rtmr3],
  ];

  const expectedEntries: Record<string, string> = expected
    ? {
        MRTD: expected.mrtd,
        RTMR0: expected.rtmr0,
        RTMR1: expected.rtmr1,
        RTMR2: expected.rtmr2,
        RTMR3: expected.rtmr3,
      }
    : {};

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
      {entries.map(([label, value]) => (
        <MeasurementRow
          key={label}
          label={label}
          value={value}
          expectedValue={expectedEntries[label]}
          showCopy={showCopyButtons}
        />
      ))}
    </div>
  );
}
