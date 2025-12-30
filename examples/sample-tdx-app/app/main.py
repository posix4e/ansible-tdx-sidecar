#!/usr/bin/env python3
"""
Sample TDX Application

A simple Flask application that:
1. Self-registers with the attestation dashboard on startup
2. Provides basic API endpoints for demonstration
3. Integrates with the TDX attestation proxy for quote generation
"""

import logging
import os
import threading

import requests
from flask import Flask, jsonify

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
TDX_PROXY_URL = os.environ.get("TDX_ATTESTATION_PROXY_URL", "http://localhost:8081")
APP_VERSION = os.environ.get("APP_VERSION", "1.0.0")

# Store registration info
registration_info = {"registered": False, "registration_id": None}


@app.route("/")
def index():
    """Home page with application info."""
    return jsonify({
        "name": "Sample TDX Application",
        "version": APP_VERSION,
        "description": "A sample application demonstrating TDX attestation and self-registration",
        "registered": registration_info["registered"],
        "registration_id": registration_info["registration_id"],
        "endpoints": {
            "/": "This page",
            "/health": "Health check",
            "/api/data": "Sample protected data",
            "/api/whoami": "Application identity info",
            "/attest": "Get TDX attestation quote",
        },
    })


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})


@app.route("/api/data")
def get_data():
    """Sample API endpoint returning protected data."""
    return jsonify({
        "data": "This is protected data from a TDX-attested application",
        "message": "If you're seeing this, you came through the attestation proxy!",
        "attestation_verified": True,
    })


@app.route("/api/whoami")
def whoami():
    """Return application identity information."""
    return jsonify({
        "app_name": os.environ.get("APP_NAME", "sample-tdx-app"),
        "github_org": os.environ.get("GITHUB_ORG", "unknown"),
        "github_repo": os.environ.get("GITHUB_REPO", "unknown"),
        "image": os.environ.get("IMAGE_REPO", "unknown"),
        "version": APP_VERSION,
        "registered": registration_info["registered"],
        "registration_id": registration_info["registration_id"],
    })


@app.route("/attest")
def attest():
    """Get TDX attestation quote from local proxy."""
    try:
        response = requests.get(f"{TDX_PROXY_URL}/quote", timeout=60)
        if response.status_code != 200:
            return jsonify({"error": "Failed to get TDX quote"}), 503

        quote_data = response.json()
        return jsonify({
            "attestation": {
                "measurements": quote_data.get("measurements", {}),
                "quote_size": quote_data.get("quote_size", 0),
                "quote_preview": quote_data.get("quote", "")[:100] + "...",
            },
            "message": "TDX attestation successful!",
        })
    except requests.RequestException as e:
        return jsonify({"error": f"TDX attestation failed: {str(e)}"}), 503


def background_register():
    """Run self-registration in background thread."""
    from register import self_register

    result = self_register()
    if result:
        registration_info["registered"] = True
        registration_info["registration_id"] = result.get("id")
        logger.info(f"Background registration complete: {result.get('id')}")
    else:
        logger.warning("Background registration failed")


if __name__ == "__main__":
    # Start self-registration in background
    logger.info("Starting background self-registration...")
    reg_thread = threading.Thread(target=background_register, daemon=True)
    reg_thread.start()

    # Run Flask app
    port = int(os.environ.get("PORT", os.environ.get("APP_PORT", 8080)))
    app.run(host="0.0.0.0", port=port)
