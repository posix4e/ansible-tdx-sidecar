// TDX Measurements
export interface TDXMeasurements {
  mrtd: string;
  rtmr0: string;
  rtmr1: string;
  rtmr2: string;
  rtmr3: string;
}

// Verification status
export type VerificationStatus = 'pending' | 'success' | 'failed' | 'partial';

// Application registration
export interface Registration {
  id: string;
  name: string;
  description: string | null;
  image_repository: string;
  image_tag: string | null;
  image_digest: string | null;
  github_org: string;
  github_repo: string;
  github_workflow: string | null;
  dockerfile_path: string;
  app_endpoint: string;
  tdx_proxy_endpoint: string;
  expected_mrtd: string | null;
  expected_rtmr0: string | null;
  expected_rtmr1: string | null;
  expected_rtmr2: string | null;
  expected_rtmr3: string | null;
  created_at: string;
  updated_at: string;
  proxy_url: string | null;
}

// Registration form data
export interface RegistrationCreate {
  name: string;
  description?: string;
  image_repository: string;
  image_tag?: string;
  image_digest?: string;
  github_org: string;
  github_repo: string;
  github_workflow?: string;
  dockerfile_path?: string;
  app_endpoint: string;
  tdx_proxy_endpoint: string;
  expected_mrtd?: string;
  expected_rtmr0?: string;
  expected_rtmr1?: string;
  expected_rtmr2?: string;
  expected_rtmr3?: string;
}

// Verification results
export interface DCAPVerificationResult {
  verified: boolean;
  status: string;
  tcb_status: string | null;
  collateral_expiry: string | null;
  error: string | null;
}

export interface GitHubVerificationResult {
  verified: boolean;
  signer_identity: string | null;
  workflow_ref: string | null;
  build_trigger: string | null;
  repository: string | null;
  error: string | null;
}

export interface MeasurementVerificationResult {
  verified: boolean;
  mrtd_match: boolean;
  rtmr0_match: boolean;
  rtmr1_match: boolean;
  rtmr2_match: boolean;
  rtmr3_match: boolean;
  actual_measurements: TDXMeasurements | null;
  expected_measurements: TDXMeasurements | null;
  error: string | null;
}

export interface VerificationResponse {
  id: string;
  registration_id: string;
  status: VerificationStatus;
  dcap: DCAPVerificationResult;
  github: GitHubVerificationResult;
  measurements: MeasurementVerificationResult;
  verification_duration_ms: number;
  created_at: string;
  error: string | null;
}

// System status
export interface SystemStatus {
  timestamp: string;
  app_name: string;
  tdx_proxy_url: string;
  database_url: string;
  tdx_available: boolean;
  tdx_status: Record<string, unknown>;
  dcap_library_available: boolean;
}
