import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getRegistrations,
  getRegistration,
  createRegistration,
  deleteRegistration,
  captureBaseline,
} from '../api/registrations';
import type { RegistrationCreate } from '../types';

export function useRegistrations() {
  return useQuery({
    queryKey: ['registrations'],
    queryFn: getRegistrations,
    staleTime: 30000,
    refetchInterval: 60000,
  });
}

export function useRegistration(id: string) {
  return useQuery({
    queryKey: ['registrations', id],
    queryFn: () => getRegistration(id),
    enabled: !!id,
  });
}

export function useCreateRegistration() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: RegistrationCreate) => createRegistration(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['registrations'] });
    },
  });
}

export function useDeleteRegistration() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteRegistration(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['registrations'] });
    },
  });
}

export function useCaptureBaseline() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (registrationId: string) => captureBaseline(registrationId),
    onSuccess: (_, registrationId) => {
      queryClient.invalidateQueries({ queryKey: ['registrations', registrationId] });
    },
  });
}
