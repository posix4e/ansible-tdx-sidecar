"""DCAP Quote Verification using Intel's QVL."""

import base64
import ctypes
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum
from threading import Lock
from typing import Optional

logger = logging.getLogger(__name__)


class QuoteVerificationResult(IntEnum):
    """SGX/TDX Quote verification result codes."""

    OK = 0
    CONFIG_NEEDED = 1
    OUT_OF_DATE = 2
    OUT_OF_DATE_CONFIG_NEEDED = 3
    INVALID_SIGNATURE = 4
    REVOKED = 5
    UNSPECIFIED = 6


@dataclass
class DCAPVerificationOutput:
    """DCAP verification output."""

    verified: bool
    status: str
    tcb_status: Optional[str]
    collateral_expiry: Optional[datetime]
    quote_body: Optional[bytes]
    error: Optional[str]


class DCAPVerifier:
    """
    TDX DCAP Quote Verifier using Intel's QVL.

    Falls back to mock verification if library is not available.
    """

    def __init__(self, library_path: str = "/usr/lib/x86_64-linux-gnu/libsgx_dcap_quoteverify.so"):
        self.library_path = library_path
        self._lib: Optional[ctypes.CDLL] = None
        self._lib_lock = Lock()
        self._lib_available: Optional[bool] = None

    def _load_library(self) -> Optional[ctypes.CDLL]:
        """Load the DCAP quote verification library."""
        with self._lib_lock:
            if self._lib is not None:
                return self._lib

            if self._lib_available is False:
                return None

            try:
                self._lib = ctypes.CDLL(self.library_path)
                self._setup_function_signatures()
                self._lib_available = True
                logger.info(f"Loaded DCAP library from {self.library_path}")
                return self._lib
            except OSError as e:
                logger.warning(f"DCAP library not available: {e}")
                self._lib_available = False
                return None

    def _setup_function_signatures(self) -> None:
        """Setup C function signatures for ctypes."""
        if self._lib is None:
            return

        # sgx_qv_verify_quote signature
        self._lib.sgx_qv_verify_quote.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),  # quote
            ctypes.c_uint32,  # quote_size
            ctypes.c_void_p,  # p_quote_collateral (NULL for auto-fetch)
            ctypes.c_int64,  # expiration_check_date
            ctypes.POINTER(ctypes.c_uint32),  # p_collateral_expiration_status
            ctypes.POINTER(ctypes.c_uint32),  # p_quote_verification_result
            ctypes.c_void_p,  # p_qve_report_info (NULL if not using QvE)
            ctypes.c_uint32,  # supplemental_data_size
            ctypes.POINTER(ctypes.c_uint8),  # p_supplemental_data
        ]
        self._lib.sgx_qv_verify_quote.restype = ctypes.c_int

        # Get supplemental data size
        self._lib.sgx_qv_get_quote_supplemental_data_size.argtypes = [
            ctypes.POINTER(ctypes.c_uint32)
        ]
        self._lib.sgx_qv_get_quote_supplemental_data_size.restype = ctypes.c_int

    def verify_quote(self, quote_b64: str) -> DCAPVerificationOutput:
        """
        Verify a TDX DCAP quote.

        Args:
            quote_b64: Base64-encoded TDX quote

        Returns:
            DCAPVerificationOutput with verification results
        """
        try:
            quote = base64.b64decode(quote_b64)
        except Exception as e:
            return DCAPVerificationOutput(
                verified=False,
                status="INVALID_FORMAT",
                tcb_status=None,
                collateral_expiry=None,
                quote_body=None,
                error=f"Invalid base64 quote: {e}",
            )

        lib = self._load_library()
        if lib is None:
            # Fall back to mock verification (checks basic structure)
            return self._mock_verify(quote)

        return self._real_verify(lib, quote)

    def _mock_verify(self, quote: bytes) -> DCAPVerificationOutput:
        """
        Mock verification when library is not available.
        Performs basic structural validation only.
        """
        # Basic quote structure validation
        if len(quote) < 560:
            return DCAPVerificationOutput(
                verified=False,
                status="INVALID_QUOTE_LENGTH",
                tcb_status=None,
                collateral_expiry=None,
                quote_body=quote,
                error=f"Quote too short: {len(quote)} bytes",
            )

        # Check quote version (should be 4 for TDX)
        version = int.from_bytes(quote[0:2], "little")
        if version != 4:
            return DCAPVerificationOutput(
                verified=False,
                status="INVALID_QUOTE_VERSION",
                tcb_status=None,
                collateral_expiry=None,
                quote_body=quote,
                error=f"Unexpected quote version: {version}",
            )

        # In mock mode, we accept structurally valid quotes
        # but warn that real DCAP verification is not available
        logger.warning("DCAP library not available - using mock verification")
        return DCAPVerificationOutput(
            verified=True,
            status="MOCK_OK",
            tcb_status="MockVerification",
            collateral_expiry=None,
            quote_body=quote,
            error="DCAP library not available - structural validation only",
        )

    def _real_verify(self, lib: ctypes.CDLL, quote: bytes) -> DCAPVerificationOutput:
        """Perform real DCAP verification using the library."""
        try:
            quote_size = len(quote)
            quote_arr = (ctypes.c_uint8 * quote_size)(*quote)

            # Get supplemental data size
            supp_size = ctypes.c_uint32(0)
            ret = lib.sgx_qv_get_quote_supplemental_data_size(ctypes.byref(supp_size))
            if ret != 0:
                supp_size.value = 0

            # Prepare output variables
            collateral_expiration_status = ctypes.c_uint32(0)
            verification_result = ctypes.c_uint32(0)

            # Supplemental data buffer
            supp_data = (
                (ctypes.c_uint8 * supp_size.value)() if supp_size.value > 0 else None
            )

            # Current time for expiration check
            current_time = int(datetime.utcnow().timestamp())

            # Verify quote (NULL collateral = auto-fetch from PCCS)
            ret = lib.sgx_qv_verify_quote(
                quote_arr,
                quote_size,
                None,  # Auto-fetch collateral
                current_time,
                ctypes.byref(collateral_expiration_status),
                ctypes.byref(verification_result),
                None,  # No QvE report
                supp_size.value,
                supp_data,
            )

            if ret != 0:
                return DCAPVerificationOutput(
                    verified=False,
                    status="ERROR",
                    tcb_status=None,
                    collateral_expiry=None,
                    quote_body=quote,
                    error=f"Quote verification failed with code: {ret}",
                )

            # Interpret result
            result_code = QuoteVerificationResult(verification_result.value)
            verified = result_code == QuoteVerificationResult.OK

            return DCAPVerificationOutput(
                verified=verified,
                status=result_code.name,
                tcb_status=self._get_tcb_status(result_code),
                collateral_expiry=None,  # Would need to parse supplemental data
                quote_body=quote,
                error=None if verified else f"Verification status: {result_code.name}",
            )

        except Exception as e:
            logger.exception("DCAP verification failed")
            return DCAPVerificationOutput(
                verified=False,
                status="EXCEPTION",
                tcb_status=None,
                collateral_expiry=None,
                quote_body=quote,
                error=str(e),
            )

    def _get_tcb_status(self, result: QuoteVerificationResult) -> str:
        """Map verification result to TCB status."""
        status_map = {
            QuoteVerificationResult.OK: "UpToDate",
            QuoteVerificationResult.CONFIG_NEEDED: "ConfigurationNeeded",
            QuoteVerificationResult.OUT_OF_DATE: "OutOfDate",
            QuoteVerificationResult.OUT_OF_DATE_CONFIG_NEEDED: "OutOfDateConfigurationNeeded",
            QuoteVerificationResult.REVOKED: "Revoked",
        }
        return status_map.get(result, "Unknown")

    @property
    def is_available(self) -> bool:
        """Check if DCAP library is available."""
        self._load_library()
        return self._lib_available is True
