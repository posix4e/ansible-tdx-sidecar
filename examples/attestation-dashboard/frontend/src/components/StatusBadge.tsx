import type { VerificationStatus } from '../types';

interface StatusBadgeProps {
  status: VerificationStatus | 'verified' | 'unverified';
  size?: 'sm' | 'md' | 'lg';
}

const statusStyles: Record<string, string> = {
  success: 'bg-green-100 text-green-800 border-green-200',
  verified: 'bg-green-100 text-green-800 border-green-200',
  partial: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  pending: 'bg-blue-100 text-blue-800 border-blue-200',
  failed: 'bg-red-100 text-red-800 border-red-200',
  unverified: 'bg-gray-100 text-gray-800 border-gray-200',
};

const sizeStyles = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-2.5 py-1 text-sm',
  lg: 'px-3 py-1.5 text-base',
};

export function StatusBadge({ status, size = 'md' }: StatusBadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full border font-medium ${
        statusStyles[status] || statusStyles.unverified
      } ${sizeStyles[size]}`}
    >
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}
