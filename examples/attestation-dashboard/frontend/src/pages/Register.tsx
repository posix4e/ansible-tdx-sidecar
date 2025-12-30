import { useForm } from 'react-hook-form';
import { useNavigate, Link } from 'react-router-dom';
import { useCreateRegistration } from '../hooks/useRegistrations';
import type { RegistrationCreate } from '../types';

export function Register() {
  const navigate = useNavigate();
  const createRegistration = useCreateRegistration();
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<RegistrationCreate>({
    defaultValues: {
      dockerfile_path: 'Dockerfile',
      github_workflow: '.github/workflows/build.yml',
    },
  });

  const onSubmit = async (data: RegistrationCreate) => {
    try {
      const registration = await createRegistration.mutateAsync(data);
      navigate(`/applications/${registration.id}`);
    } catch (error) {
      console.error('Registration failed:', error);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <Link to="/" className="text-tdx-primary hover:underline">&larr; Back to Dashboard</Link>
      </div>

      <h1 className="text-2xl font-bold mb-6">Register New Application</h1>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div className="bg-white p-6 rounded-lg border space-y-4">
          <h2 className="font-semibold text-gray-700">Basic Information</h2>

          <div>
            <label className="block text-sm font-medium text-gray-700">Name *</label>
            <input {...register('name', { required: 'Name is required' })} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-tdx-primary focus:ring-tdx-primary" />
            {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Description</label>
            <textarea {...register('description')} rows={2} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-tdx-primary focus:ring-tdx-primary" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg border space-y-4">
          <h2 className="font-semibold text-gray-700">GitHub Repository</h2>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Organization *</label>
              <input {...register('github_org', { required: 'Required' })} placeholder="owner" className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-tdx-primary focus:ring-tdx-primary" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Repository *</label>
              <input {...register('github_repo', { required: 'Required' })} placeholder="repo-name" className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-tdx-primary focus:ring-tdx-primary" />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Workflow Path</label>
            <input {...register('github_workflow')} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-tdx-primary focus:ring-tdx-primary" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg border space-y-4">
          <h2 className="font-semibold text-gray-700">Container Image</h2>

          <div>
            <label className="block text-sm font-medium text-gray-700">Image Repository *</label>
            <input {...register('image_repository', { required: 'Required' })} placeholder="ghcr.io/org/image" className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-tdx-primary focus:ring-tdx-primary" />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Tag</label>
              <input {...register('image_tag')} placeholder="latest" className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-tdx-primary focus:ring-tdx-primary" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Digest</label>
              <input {...register('image_digest')} placeholder="sha256:..." className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-tdx-primary focus:ring-tdx-primary" />
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg border space-y-4">
          <h2 className="font-semibold text-gray-700">Endpoints</h2>

          <div>
            <label className="block text-sm font-medium text-gray-700">Application Endpoint *</label>
            <input {...register('app_endpoint', { required: 'Required' })} placeholder="http://10.0.0.5:8080" className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-tdx-primary focus:ring-tdx-primary" />
            <p className="mt-1 text-xs text-gray-500">URL where the application is accessible</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">TDX Proxy Endpoint *</label>
            <input {...register('tdx_proxy_endpoint', { required: 'Required' })} placeholder="http://10.0.0.5:8081" className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-tdx-primary focus:ring-tdx-primary" />
            <p className="mt-1 text-xs text-gray-500">URL of the TDX attestation proxy</p>
          </div>
        </div>

        <div className="flex justify-end gap-4">
          <Link to="/" className="px-4 py-2 text-gray-700 hover:text-gray-900">Cancel</Link>
          <button type="submit" disabled={isSubmitting} className="px-6 py-2 bg-tdx-primary text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
            {isSubmitting ? 'Registering...' : 'Register Application'}
          </button>
        </div>
      </form>
    </div>
  );
}
