"""GitHub Artifact Attestation Verification."""

import asyncio
import json
import logging
import subprocess
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class GitHubVerificationOutput:
    """GitHub attestation verification output."""

    verified: bool
    signer_identity: Optional[str]
    workflow_ref: Optional[str]
    build_trigger: Optional[str]
    repository: Optional[str]
    error: Optional[str]


class GitHubAttestationVerifier:
    """
    Verifier for GitHub Artifact Attestations.

    Uses GitHub REST API to fetch attestation bundles and verify them.
    """

    GITHUB_API_BASE = "https://api.github.com"
    GITHUB_OIDC_ISSUER = "https://token.actions.githubusercontent.com"

    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize verifier.

        Args:
            github_token: GitHub PAT for API access (required for private repos)
        """
        self.github_token = github_token
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            headers = {"Accept": "application/vnd.github+json"}
            if self.github_token:
                headers["Authorization"] = f"Bearer {self.github_token}"
            self._client = httpx.AsyncClient(headers=headers, timeout=30.0)
        return self._client

    async def verify_image_attestation(
        self,
        image_digest: str,
        expected_org: str,
        expected_repo: str,
        expected_workflow: Optional[str] = None,
    ) -> GitHubVerificationOutput:
        """
        Verify GitHub artifact attestation for a container image.

        Args:
            image_digest: Container image digest (sha256:...)
            expected_org: Expected GitHub org/user
            expected_repo: Expected repository name
            expected_workflow: Optional expected workflow path

        Returns:
            GitHubVerificationOutput with verification results
        """
        try:
            # 1. Try CLI-based verification first (more reliable)
            cli_result = await self._verify_with_cli(
                image_digest, expected_org, expected_repo, expected_workflow
            )
            if cli_result.verified or cli_result.error != "gh CLI not available":
                return cli_result

            # 2. Fall back to API-based verification
            return await self._verify_with_api(
                image_digest, expected_org, expected_repo, expected_workflow
            )

        except Exception as e:
            logger.exception("GitHub attestation verification failed")
            return GitHubVerificationOutput(
                verified=False,
                signer_identity=None,
                workflow_ref=None,
                build_trigger=None,
                repository=None,
                error=str(e),
            )

    async def _verify_with_cli(
        self,
        image_digest: str,
        expected_org: str,
        expected_repo: str,
        expected_workflow: Optional[str],
    ) -> GitHubVerificationOutput:
        """
        Verify using GitHub CLI (requires gh >= 2.49.0).

        gh attestation verify <artifact> --owner <org> [--repo <repo>]
        """
        # Normalize digest
        if not image_digest.startswith("sha256:"):
            image_digest = f"sha256:{image_digest}"

        # Build artifact reference (for OCI images)
        artifact_ref = f"oci://{expected_org}/{expected_repo}@{image_digest}"

        cmd = [
            "gh",
            "attestation",
            "verify",
            artifact_ref,
            "--owner",
            expected_org,
            "--format",
            "json",
        ]

        if expected_workflow:
            cmd.extend(["--signer-workflow", expected_workflow])

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await result.communicate()

            if result.returncode == 0:
                # Parse JSON output
                try:
                    data = json.loads(stdout.decode())
                    # Extract details from verification result
                    return GitHubVerificationOutput(
                        verified=True,
                        signer_identity=data.get("verificationResult", {}).get(
                            "signedEntityCertificate", {}
                        ).get("subjectAlternativeName"),
                        workflow_ref=data.get("verificationResult", {}).get(
                            "statement", {}
                        ).get("predicateType"),
                        build_trigger=None,
                        repository=f"{expected_org}/{expected_repo}",
                        error=None,
                    )
                except json.JSONDecodeError:
                    return GitHubVerificationOutput(
                        verified=True,
                        signer_identity=None,
                        workflow_ref=expected_workflow,
                        build_trigger=None,
                        repository=f"{expected_org}/{expected_repo}",
                        error=None,
                    )
            else:
                error_msg = stderr.decode() if stderr else "Verification failed"
                return GitHubVerificationOutput(
                    verified=False,
                    signer_identity=None,
                    workflow_ref=None,
                    build_trigger=None,
                    repository=None,
                    error=error_msg.strip(),
                )

        except FileNotFoundError:
            return GitHubVerificationOutput(
                verified=False,
                signer_identity=None,
                workflow_ref=None,
                build_trigger=None,
                repository=None,
                error="gh CLI not available",
            )

    async def _verify_with_api(
        self,
        image_digest: str,
        expected_org: str,
        expected_repo: str,
        expected_workflow: Optional[str],
    ) -> GitHubVerificationOutput:
        """
        Verify using GitHub REST API.

        Fetches attestation bundle and performs basic validation.
        Note: Full Sigstore verification requires sigstore-python.
        """
        # Normalize digest
        if not image_digest.startswith("sha256:"):
            image_digest = f"sha256:{image_digest}"

        client = await self._get_client()

        try:
            # Fetch attestation from GitHub API
            url = f"{self.GITHUB_API_BASE}/users/{expected_org}/attestations/{image_digest}"
            response = await client.get(url)

            if response.status_code == 404:
                return GitHubVerificationOutput(
                    verified=False,
                    signer_identity=None,
                    workflow_ref=None,
                    build_trigger=None,
                    repository=None,
                    error="No attestation found for image digest",
                )

            response.raise_for_status()
            data = response.json()

            attestations = data.get("attestations", [])
            if not attestations:
                return GitHubVerificationOutput(
                    verified=False,
                    signer_identity=None,
                    workflow_ref=None,
                    build_trigger=None,
                    repository=None,
                    error="No attestations in response",
                )

            # Get first attestation bundle
            bundle = attestations[0].get("bundle", {})

            # Extract verification material
            verification_material = bundle.get("verificationMaterial", {})
            certificate = verification_material.get("certificate", {})

            # For full verification, we would use sigstore-python here
            # For now, we do basic validation that an attestation exists
            # and check the repository matches

            # Check if the attestation is for the expected repository
            # This is a simplified check - full verification would validate the signature
            ds_envelope = bundle.get("dsseEnvelope", {})
            payload_b64 = ds_envelope.get("payload", "")

            if payload_b64:
                import base64

                try:
                    payload = json.loads(base64.b64decode(payload_b64))
                    predicate = payload.get("predicate", {})
                    build_def = predicate.get("buildDefinition", {})
                    external_params = build_def.get("externalParameters", {})
                    workflow = external_params.get("workflow", {})

                    repo_ref = workflow.get("repository", "")
                    workflow_ref = workflow.get("ref", "")

                    # Validate repository matches
                    expected_repo_full = f"https://github.com/{expected_org}/{expected_repo}"
                    if repo_ref and expected_repo_full.lower() not in repo_ref.lower():
                        return GitHubVerificationOutput(
                            verified=False,
                            signer_identity=None,
                            workflow_ref=workflow_ref,
                            build_trigger=None,
                            repository=repo_ref,
                            error=f"Repository mismatch: expected {expected_repo_full}, got {repo_ref}",
                        )

                    # Basic validation passed
                    return GitHubVerificationOutput(
                        verified=True,
                        signer_identity=None,  # Would need sigstore-python to extract
                        workflow_ref=workflow_ref,
                        build_trigger=external_params.get("github", {}).get("event_name"),
                        repository=f"{expected_org}/{expected_repo}",
                        error="API-based verification (signature not fully verified)",
                    )
                except Exception as e:
                    logger.warning(f"Failed to parse attestation payload: {e}")

            # Attestation found but couldn't fully validate
            return GitHubVerificationOutput(
                verified=True,
                signer_identity=None,
                workflow_ref=None,
                build_trigger=None,
                repository=f"{expected_org}/{expected_repo}",
                error="Attestation found but payload parsing failed",
            )

        except httpx.HTTPStatusError as e:
            return GitHubVerificationOutput(
                verified=False,
                signer_identity=None,
                workflow_ref=None,
                build_trigger=None,
                repository=None,
                error=f"GitHub API error: {e.response.status_code}",
            )

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
