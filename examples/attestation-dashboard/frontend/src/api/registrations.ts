import { api } from './client';
import type { Registration, RegistrationCreate } from '../types';

export const getRegistrations = () => api.get<Registration[]>('/registrations');

export const getRegistration = (id: string) => api.get<Registration>(`/registrations/${id}`);

export const createRegistration = (data: RegistrationCreate) =>
  api.post<Registration>('/registrations', data);

export const updateRegistration = (id: string, data: Partial<RegistrationCreate>) =>
  api.put<Registration>(`/registrations/${id}`, data);

export const deleteRegistration = (id: string) => api.delete(`/registrations/${id}`);

export const captureBaseline = (registrationId: string) =>
  api.post<{ registration_id: string; measurements: Record<string, string>; captured_at: string }>(
    '/verify/baseline',
    { registration_id: registrationId },
  );
