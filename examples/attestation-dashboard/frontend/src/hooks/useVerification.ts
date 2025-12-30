import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { verifyRegistration, getVerificationHistory, getSystemStatus } from '../api/verification';

export function useVerifyRegistration() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ registrationId, quoteBase64 }: { registrationId: string; quoteBase64?: string }) =>
      verifyRegistration(registrationId, quoteBase64),
    onSuccess: (_, { registrationId }) => {
      queryClient.invalidateQueries({ queryKey: ['verifications', registrationId] });
    },
  });
}

export function useVerificationHistory(registrationId?: string) {
  return useQuery({
    queryKey: ['verifications', registrationId],
    queryFn: () => getVerificationHistory(registrationId),
    staleTime: 10000,
  });
}

export function useSystemStatus() {
  return useQuery({
    queryKey: ['status'],
    queryFn: getSystemStatus,
    staleTime: 30000,
    refetchInterval: 60000,
  });
}
