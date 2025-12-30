"""Full chain verification orchestration."""

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

from ..api.schemas import (
    DCAPVerificationResult,
    GitHubVerificationResult,
    MeasurementVerificationResult,
    TDXMeasurements,
)
from ..config import Settings
from ..db.models import Registration
from .dcap_verifier import DCAPVerifier
from .github_verifier import GitHubAttestationVerifier
from .measurement_verifier import MeasurementVerifier
from .measurement_verifier import TDXMeasurements as MeasurementData

logger = logging.getLogger(__name__)


@dataclass
class ChainVerificationResult:
    """Full chain verification result."""

    dcap: DCAPVerificationResult
    github: GitHubVerificationResult
    measurements: MeasurementVerificationResult


class ChainVerifier:
    """
    Orchestrates full chain TDX attestation verification.

    Verification chain:
    1. DCAP quote verification (cryptographic validity)
    2. GitHub attestation verification (build provenance)
    3. Measurement verification (expected vs actual)
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.dcap_verifier = DCAPVerifier(settings.dcap_library_path)
        self.github_verifier = GitHubAttestationVerifier(settings.github_token)
        self.measurement_verifier = MeasurementVerifier()

    async def verify(
        self,
        registration: Registration,
        quote_base64: Optional[str] = None,
        report_data: Optional[str] = None,
    ) -> ChainVerificationResult:
        """
        Perform full chain verification.

        Args:
            registration: The application registration to verify
            quote_base64: Optional pre-fetched quote. If not provided, fetches from proxy.
            report_data: Optional report data for quote generation

        Returns:
            ChainVerificationResult with all verification outcomes
        """
        # Step 1: Get quote if not provided
        actual_measurements: Optional[MeasurementData] = None
        if not quote_base64:
            try:
                quote_base64, actual_measurements = await self.measurement_verifier.fetch_quote(
                    registration.tdx_proxy_endpoint, report_data
                )
            except Exception as e:
                logger.error(f"Failed to fetch quote: {e}")
                return ChainVerificationResult(
                    dcap=DCAPVerificationResult(
                        verified=False,
                        status="FETCH_FAILED",
                        error=f"Failed to fetch quote: {e}",
                    ),
                    github=GitHubVerificationResult(
                        verified=False,
                        error="Skipped due to quote fetch failure",
                    ),
                    measurements=MeasurementVerificationResult(
                        verified=False,
                        error="Skipped due to quote fetch failure",
                    ),
                )

        # Step 2: Run DCAP and GitHub verification in parallel
        dcap_task = asyncio.create_task(
            asyncio.to_thread(self.dcap_verifier.verify_quote, quote_base64)
        )
        github_task = asyncio.create_task(
            self._verify_github(registration)
        )

        dcap_output, github_output = await asyncio.gather(dcap_task, github_task)

        # Convert DCAP output to schema
        dcap_result = DCAPVerificationResult(
            verified=dcap_output.verified,
            status=dcap_output.status,
            tcb_status=dcap_output.tcb_status,
            collateral_expiry=dcap_output.collateral_expiry,
            error=dcap_output.error,
        )

        # Convert GitHub output to schema
        github_result = GitHubVerificationResult(
            verified=github_output.verified,
            signer_identity=github_output.signer_identity,
            workflow_ref=github_output.workflow_ref,
            build_trigger=github_output.build_trigger,
            repository=github_output.repository,
            error=github_output.error,
        )

        # Step 3: Measurement verification
        measurement_result = await self._verify_measurements(
            registration, quote_base64, actual_measurements
        )

        return ChainVerificationResult(
            dcap=dcap_result,
            github=github_result,
            measurements=measurement_result,
        )

    async def _verify_github(self, registration: Registration) -> "GitHubVerificationOutput":
        """Verify GitHub attestation for the registration."""
        from .github_verifier import GitHubVerificationOutput

        # Skip if no image digest
        if not registration.image_digest:
            return GitHubVerificationOutput(
                verified=False,
                signer_identity=None,
                workflow_ref=None,
                build_trigger=None,
                repository=None,
                error="No image digest configured for GitHub attestation verification",
            )

        return await self.github_verifier.verify_image_attestation(
            image_digest=registration.image_digest,
            expected_org=registration.github_org,
            expected_repo=registration.github_repo,
            expected_workflow=registration.github_workflow,
        )

    async def _verify_measurements(
        self,
        registration: Registration,
        quote_base64: str,
        actual_measurements: Optional[MeasurementData],
    ) -> MeasurementVerificationResult:
        """Verify TDX measurements against expected values."""
        # Extract measurements from quote if not already available
        if actual_measurements is None:
            try:
                actual_measurements = self.measurement_verifier.extract_from_base64(quote_base64)
            except Exception as e:
                return MeasurementVerificationResult(
                    verified=False,
                    error=f"Failed to extract measurements: {e}",
                )

        # Check if expected measurements are configured
        if not registration.expected_mrtd:
            return MeasurementVerificationResult(
                verified=False,
                actual_measurements=TDXMeasurements(
                    mrtd=actual_measurements.mrtd,
                    rtmr0=actual_measurements.rtmr0,
                    rtmr1=actual_measurements.rtmr1,
                    rtmr2=actual_measurements.rtmr2,
                    rtmr3=actual_measurements.rtmr3,
                ),
                error="No expected measurements configured. Use /api/v1/verify/baseline to capture.",
            )

        expected = MeasurementData(
            mrtd=registration.expected_mrtd,
            rtmr0=registration.expected_rtmr0 or "",
            rtmr1=registration.expected_rtmr1 or "",
            rtmr2=registration.expected_rtmr2 or "",
            rtmr3=registration.expected_rtmr3 or "",
        )

        comparison = self.measurement_verifier.compare_measurements(
            actual=actual_measurements,
            expected=expected,
            skip_rtmr3=True,  # RTMR3 is often dynamic
        )

        return MeasurementVerificationResult(
            verified=comparison.verified,
            mrtd_match=comparison.mrtd_match,
            rtmr0_match=comparison.rtmr0_match,
            rtmr1_match=comparison.rtmr1_match,
            rtmr2_match=comparison.rtmr2_match,
            rtmr3_match=comparison.rtmr3_match,
            actual_measurements=TDXMeasurements(
                mrtd=actual_measurements.mrtd,
                rtmr0=actual_measurements.rtmr0,
                rtmr1=actual_measurements.rtmr1,
                rtmr2=actual_measurements.rtmr2,
                rtmr3=actual_measurements.rtmr3,
            ),
            expected_measurements=TDXMeasurements(
                mrtd=expected.mrtd,
                rtmr0=expected.rtmr0,
                rtmr1=expected.rtmr1,
                rtmr2=expected.rtmr2,
                rtmr3=expected.rtmr3,
            ),
            error=comparison.error,
        )

    async def close(self) -> None:
        """Close resources."""
        await self.github_verifier.close()
