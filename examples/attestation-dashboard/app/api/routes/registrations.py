"""Registration CRUD endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...db import Registration, get_db
from ..schemas import RegistrationCreate, RegistrationResponse, RegistrationUpdate

router = APIRouter()


def _add_proxy_url(registration: Registration, request: Request) -> RegistrationResponse:
    """Add computed proxy URL to registration response."""
    response = RegistrationResponse.model_validate(registration)
    base_url = str(request.base_url).rstrip("/")
    response.proxy_url = f"{base_url}/proxy/{registration.id}"
    return response


@router.get("", response_model=List[RegistrationResponse])
async def list_registrations(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
) -> List[RegistrationResponse]:
    """List all registered applications."""
    result = await db.execute(
        select(Registration).offset(skip).limit(limit).order_by(Registration.created_at.desc())
    )
    registrations = result.scalars().all()
    return [_add_proxy_url(r, request) for r in registrations]


@router.post("", response_model=RegistrationResponse, status_code=201)
async def create_registration(
    request: Request,
    data: RegistrationCreate,
    db: AsyncSession = Depends(get_db),
) -> RegistrationResponse:
    """Register a new application for attestation verification."""
    registration = Registration(
        name=data.name,
        description=data.description,
        image_repository=data.image_repository,
        image_tag=data.image_tag,
        image_digest=data.image_digest,
        github_org=data.github_org,
        github_repo=data.github_repo,
        github_workflow=data.github_workflow,
        dockerfile_path=data.dockerfile_path,
        app_endpoint=data.app_endpoint,
        tdx_proxy_endpoint=data.tdx_proxy_endpoint,
        expected_mrtd=data.expected_mrtd,
        expected_rtmr0=data.expected_rtmr0,
        expected_rtmr1=data.expected_rtmr1,
        expected_rtmr2=data.expected_rtmr2,
        expected_rtmr3=data.expected_rtmr3,
    )
    db.add(registration)
    await db.flush()
    await db.refresh(registration)
    return _add_proxy_url(registration, request)


@router.get("/{registration_id}", response_model=RegistrationResponse)
async def get_registration(
    request: Request,
    registration_id: str,
    db: AsyncSession = Depends(get_db),
) -> RegistrationResponse:
    """Get a specific registration by ID."""
    result = await db.execute(
        select(Registration).where(Registration.id == registration_id)
    )
    registration = result.scalar_one_or_none()
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")
    return _add_proxy_url(registration, request)


@router.put("/{registration_id}", response_model=RegistrationResponse)
async def update_registration(
    request: Request,
    registration_id: str,
    data: RegistrationUpdate,
    db: AsyncSession = Depends(get_db),
) -> RegistrationResponse:
    """Update an existing registration."""
    result = await db.execute(
        select(Registration).where(Registration.id == registration_id)
    )
    registration = result.scalar_one_or_none()
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")

    # Update only provided fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(registration, field, value)

    await db.flush()
    await db.refresh(registration)
    return _add_proxy_url(registration, request)


@router.delete("/{registration_id}", status_code=204)
async def delete_registration(
    registration_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a registration."""
    result = await db.execute(
        select(Registration).where(Registration.id == registration_id)
    )
    registration = result.scalar_one_or_none()
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")

    await db.delete(registration)
