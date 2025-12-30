import { api } from './client';
import type { VerificationResponse, SystemStatus } from '../types';

export const verifyRegistration = (registrationId: string, quoteBase64?: string) =>
  api.post<VerificationResponse>('/verify', {
    registration_id: registrationId,
    quote_base64: quoteBase64,
  });

export const getVerificationHistory = (registrationId?: string, skip = 0, limit = 50) => {
  const params = new URLSearchParams();
  if (registrationId) params.set('registration_id', registrationId);
  params.set('skip', skip.toString());
  params.set('limit', limit.toString());
  return api.get<VerificationResponse[]>(`/verify/history?${params}`);
};

export const getSystemStatus = () =>
  fetch('/status').then((r) => r.json()) as Promise<SystemStatus>;
