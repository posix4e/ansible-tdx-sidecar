"""Verification endpoints."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...config import get_settings
from ...db import Registration, VerificationLog, VerificationStatus, get_db
from ..schemas import (
    BaselineRequest,
    BaselineResponse,
    TDXMeasurements,
    VerificationRequest,
    VerificationResponse,
)

router = APIRouter()
settings = get_settings()


@router.post("", response_model=VerificationResponse)
async def verify_full_chain(
    data: VerificationRequest,
    db: AsyncSession = Depends(get_db),
) -> VerificationResponse:
    """
    Perform full chain verification:
    1. DCAP quote verification
    2. GitHub attestation verification
    3. Measurement comparison
    """
    from ...core.chain_verifier import ChainVerifier

    # Get registration
    result = await db.execute(
        select(Registration).where(Registration.id == data.registration_id)
    )
    registration = result.scalar_one_or_none()
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")

    # Perform verification
    verifier = ChainVerifier(settings)
    start_time = datetime.utcnow()

    verification_result = await verifier.verify(
        registration=registration,
        quote_base64=data.quote_base64,
        report_data=data.report_data,
    )

    duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

    # Determine overall status
    if verification_result.dcap.verified and verification_result.github.verified and verification_result.measurements.verified:
        status = VerificationStatus.SUCCESS
    elif verification_result.dcap.verified or verification_result.github.verified or verification_result.measurements.verified:
        status = VerificationStatus.PARTIAL
    else:
        status = VerificationStatus.FAILED

    # Create verification log
    log = VerificationLog(
        registration_id=registration.id,
        status=status,
        dcap_verified=verification_result.dcap.verified,
        dcap_status=verification_result.dcap.status,
        dcap_tcb_status=verification_result.dcap.tcb_status,
        github_verified=verification_result.github.verified,
        github_signer_identity=verification_result.github.signer_identity,
        github_workflow_ref=verification_result.github.workflow_ref,
        github_build_trigger=verification_result.github.build_trigger,
        measurements_verified=verification_result.measurements.verified,
        actual_mrtd=verification_result.measurements.actual_measurements.mrtd if verification_result.measurements.actual_measurements else None,
        actual_rtmr0=verification_result.measurements.actual_measurements.rtmr0 if verification_result.measurements.actual_measurements else None,
        actual_rtmr1=verification_result.measurements.actual_measurements.rtmr1 if verification_result.measurements.actual_measurements else None,
        actual_rtmr2=verification_result.measurements.actual_measurements.rtmr2 if verification_result.measurements.actual_measurements else None,
        actual_rtmr3=verification_result.measurements.actual_measurements.rtmr3 if verification_result.measurements.actual_measurements else None,
        raw_quote=data.quote_base64,
        verification_duration_ms=duration_ms,
    )
    db.add(log)
    await db.flush()
    await db.refresh(log)

    return VerificationResponse(
        id=log.id,
        registration_id=registration.id,
        status=status,
        dcap=verification_result.dcap,
        github=verification_result.github,
        measurements=verification_result.measurements,
        verification_duration_ms=duration_ms,
        created_at=log.created_at,
    )


@router.get("/history", response_model=List[VerificationResponse])
async def get_verification_history(
    registration_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> List[VerificationResponse]:
    """Get verification history, optionally filtered by registration."""
    query = select(VerificationLog).order_by(VerificationLog.created_at.desc())
    if registration_id:
        query = query.where(VerificationLog.registration_id == registration_id)
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    logs = result.scalars().all()

    return [
        VerificationResponse(
            id=log.id,
            registration_id=log.registration_id,
            status=log.status,
            dcap={
                "verified": log.dcap_verified,
                "status": log.dcap_status or "UNKNOWN",
                "tcb_status": log.dcap_tcb_status,
            },
            github={
                "verified": log.github_verified,
                "signer_identity": log.github_signer_identity,
                "workflow_ref": log.github_workflow_ref,
                "build_trigger": log.github_build_trigger,
            },
            measurements={
                "verified": log.measurements_verified,
                "mrtd_match": log.measurements_verified,
                "rtmr0_match": log.measurements_verified,
                "rtmr1_match": log.measurements_verified,
                "rtmr2_match": log.measurements_verified,
                "rtmr3_match": log.measurements_verified,
                "actual_measurements": TDXMeasurements(
                    mrtd=log.actual_mrtd or "",
                    rtmr0=log.actual_rtmr0 or "",
                    rtmr1=log.actual_rtmr1 or "",
                    rtmr2=log.actual_rtmr2 or "",
                    rtmr3=log.actual_rtmr3 or "",
                ) if log.actual_mrtd else None,
            },
            verification_duration_ms=log.verification_duration_ms or 0,
            created_at=log.created_at,
        )
        for log in logs
    ]


@router.post("/baseline", response_model=BaselineResponse)
async def capture_baseline(
    data: BaselineRequest,
    db: AsyncSession = Depends(get_db),
) -> BaselineResponse:
    """
    Capture baseline measurements from a trusted deployment.
    This sets the expected measurements for future verifications.
    """
    from ...core.measurement_verifier import MeasurementVerifier

    # Get registration
    result = await db.execute(
        select(Registration).where(Registration.id == data.registration_id)
    )
    registration = result.scalar_one_or_none()
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")

    # Fetch current measurements from TDX proxy
    verifier = MeasurementVerifier()
    measurements = await verifier.fetch_measurements(registration.tdx_proxy_endpoint)

    # Update registration with baseline measurements
    registration.expected_mrtd = measurements.mrtd
    registration.expected_rtmr0 = measurements.rtmr0
    registration.expected_rtmr1 = measurements.rtmr1
    registration.expected_rtmr2 = measurements.rtmr2
    registration.expected_rtmr3 = measurements.rtmr3

    await db.flush()

    return BaselineResponse(
        registration_id=registration.id,
        measurements=measurements,
        captured_at=datetime.utcnow(),
    )
