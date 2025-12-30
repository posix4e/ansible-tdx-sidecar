"""TDX measurement extraction and verification."""

import base64
from dataclasses import dataclass
from typing import Optional

import httpx


@dataclass
class TDXMeasurements:
    """TDX measurement registers."""

    mrtd: str  # 48 bytes hex (96 chars)
    rtmr0: str
    rtmr1: str
    rtmr2: str
    rtmr3: str


@dataclass
class MeasurementComparisonResult:
    """Result of measurement comparison."""

    verified: bool
    mrtd_match: bool
    rtmr0_match: bool
    rtmr1_match: bool
    rtmr2_match: bool
    rtmr3_match: bool
    actual: Optional[TDXMeasurements]
    expected: Optional[TDXMeasurements]
    error: Optional[str]


class MeasurementVerifier:
    """
    Verifier for TDX measurements.

    Extracts measurements from TDX quotes and compares against expected values.
    """

    # TDX Quote v4 offsets
    QUOTE_HEADER_SIZE = 48
    TD_REPORT_OFFSET = QUOTE_HEADER_SIZE
    MRTD_OFFSET = TD_REPORT_OFFSET + 128  # 176
    RTMR_OFFSET = TD_REPORT_OFFSET + 320  # 368
    RTMR_SIZE = 48  # Each RTMR is 48 bytes

    def extract_measurements(self, quote: bytes) -> TDXMeasurements:
        """
        Extract TDX measurements from a quote.

        Args:
            quote: Raw TDX quote bytes

        Returns:
            TDXMeasurements with extracted values
        """
        if len(quote) < 560:
            raise ValueError(f"Quote too short: {len(quote)} bytes (minimum 560)")

        return TDXMeasurements(
            mrtd=quote[self.MRTD_OFFSET : self.MRTD_OFFSET + 48].hex(),
            rtmr0=quote[self.RTMR_OFFSET : self.RTMR_OFFSET + 48].hex(),
            rtmr1=quote[self.RTMR_OFFSET + 48 : self.RTMR_OFFSET + 96].hex(),
            rtmr2=quote[self.RTMR_OFFSET + 96 : self.RTMR_OFFSET + 144].hex(),
            rtmr3=quote[self.RTMR_OFFSET + 144 : self.RTMR_OFFSET + 192].hex(),
        )

    def extract_from_base64(self, quote_b64: str) -> TDXMeasurements:
        """Extract measurements from base64-encoded quote."""
        quote = base64.b64decode(quote_b64)
        return self.extract_measurements(quote)

    def compare_measurements(
        self,
        actual: TDXMeasurements,
        expected: TDXMeasurements,
        skip_rtmr3: bool = True,  # RTMR3 is often application-defined
    ) -> MeasurementComparisonResult:
        """
        Compare actual vs expected measurements.

        Args:
            actual: Measurements extracted from quote
            expected: Expected measurements from registration
            skip_rtmr3: Skip RTMR3 comparison (often dynamic)

        Returns:
            MeasurementComparisonResult
        """
        mrtd_match = actual.mrtd.lower() == expected.mrtd.lower()
        rtmr0_match = actual.rtmr0.lower() == expected.rtmr0.lower()
        rtmr1_match = actual.rtmr1.lower() == expected.rtmr1.lower()
        rtmr2_match = actual.rtmr2.lower() == expected.rtmr2.lower()
        rtmr3_match = skip_rtmr3 or (actual.rtmr3.lower() == expected.rtmr3.lower())

        all_match = mrtd_match and rtmr0_match and rtmr1_match and rtmr2_match and rtmr3_match

        error = None
        if not all_match:
            mismatches = []
            if not mrtd_match:
                mismatches.append("MRTD")
            if not rtmr0_match:
                mismatches.append("RTMR0")
            if not rtmr1_match:
                mismatches.append("RTMR1")
            if not rtmr2_match:
                mismatches.append("RTMR2")
            if not rtmr3_match:
                mismatches.append("RTMR3")
            error = f"Measurement mismatch in: {', '.join(mismatches)}"

        return MeasurementComparisonResult(
            verified=all_match,
            mrtd_match=mrtd_match,
            rtmr0_match=rtmr0_match,
            rtmr1_match=rtmr1_match,
            rtmr2_match=rtmr2_match,
            rtmr3_match=rtmr3_match,
            actual=actual,
            expected=expected,
            error=error,
        )

    async def fetch_measurements(self, tdx_proxy_url: str) -> TDXMeasurements:
        """
        Fetch measurements from a TDX proxy endpoint.

        Args:
            tdx_proxy_url: URL of the TDX attestation proxy

        Returns:
            TDXMeasurements from the proxy's quote endpoint
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{tdx_proxy_url}/quote", timeout=60.0)
            response.raise_for_status()
            data = response.json()

            # The proxy returns measurements directly
            measurements = data.get("measurements", {})
            return TDXMeasurements(
                mrtd=measurements.get("mrtd", ""),
                rtmr0=measurements.get("rtmr0", ""),
                rtmr1=measurements.get("rtmr1", ""),
                rtmr2=measurements.get("rtmr2", ""),
                rtmr3=measurements.get("rtmr3", ""),
            )

    async def fetch_quote(self, tdx_proxy_url: str, report_data: Optional[str] = None) -> tuple[str, TDXMeasurements]:
        """
        Fetch quote and measurements from TDX proxy.

        Args:
            tdx_proxy_url: URL of the TDX attestation proxy
            report_data: Optional base64-encoded report data

        Returns:
            Tuple of (quote_base64, measurements)
        """
        async with httpx.AsyncClient() as client:
            if report_data:
                response = await client.post(
                    f"{tdx_proxy_url}/quote",
                    json={"reportData": report_data},
                    timeout=60.0,
                )
            else:
                response = await client.get(f"{tdx_proxy_url}/quote", timeout=60.0)

            response.raise_for_status()
            data = response.json()

            quote_b64 = data.get("quote", "")
            measurements = data.get("measurements", {})

            return quote_b64, TDXMeasurements(
                mrtd=measurements.get("mrtd", ""),
                rtmr0=measurements.get("rtmr0", ""),
                rtmr1=measurements.get("rtmr1", ""),
                rtmr2=measurements.get("rtmr2", ""),
                rtmr3=measurements.get("rtmr3", ""),
            )
