import { Link } from 'react-router-dom';
import type { Registration } from '../types';
import { StatusBadge } from './StatusBadge';

interface RegistrationCardProps {
  registration: Registration;
  onDelete?: () => void;
}

export function RegistrationCard({ registration, onDelete }: RegistrationCardProps) {
  const hasBaseline = !!registration.expected_mrtd;

  return (
    <div className="bg-white rounded-lg border shadow-sm hover:shadow-md transition-shadow">
      <div className="p-4">
        <div className="flex items-start justify-between">
          <div>
            <Link
              to={`/applications/${registration.id}`}
              className="text-lg font-semibold text-gray-900 hover:text-tdx-primary"
            >
              {registration.name}
            </Link>
            <p className="text-sm text-gray-500 mt-1">{registration.description}</p>
          </div>
          <StatusBadge status={hasBaseline ? 'verified' : 'unverified'} />
        </div>

        <div className="mt-4 space-y-2 text-sm">
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-gray-400" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
            </svg>
            <span className="text-gray-600">
              {registration.github_org}/{registration.github_repo}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" />
            </svg>
            <span className="text-gray-600 truncate" title={registration.image_repository}>
              {registration.image_repository}:{registration.image_tag}
            </span>
          </div>

          {registration.proxy_url && (
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
              </svg>
              <code className="text-xs bg-gray-100 px-2 py-1 rounded truncate">
                {registration.proxy_url}
              </code>
            </div>
          )}
        </div>
      </div>

      <div className="border-t px-4 py-3 flex justify-between items-center bg-gray-50">
        <span className="text-xs text-gray-500">
          Created {new Date(registration.created_at).toLocaleDateString()}
        </span>
        <div className="flex gap-2">
          <Link
            to={`/applications/${registration.id}`}
            className="text-sm text-tdx-primary hover:underline"
          >
            View Details
          </Link>
          {onDelete && (
            <button onClick={onDelete} className="text-sm text-red-600 hover:underline">
              Delete
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
