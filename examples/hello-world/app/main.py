#!/usr/bin/env python3
"""
Hello World TDX Application

A simple Flask application demonstrating TDX attestation integration.
"""

import base64
import json
import os

import requests
from flask import Flask, jsonify

app = Flask(__name__)

# TDX Attestation Proxy URL (provided via environment variable)
TDX_PROXY_URL = os.environ.get('TDX_ATTESTATION_PROXY_URL', 'http://host.docker.internal:8081')


@app.route('/')
def index():
    """Home page."""
    return jsonify({
        'name': 'Hello World TDX App',
        'description': 'A simple application demonstrating TDX attestation',
        'endpoints': {
            '/': 'This page',
            '/health': 'Health check endpoint',
            '/attest': 'Get TDX attestation quote',
            '/status': 'Check TDX availability',
        }
    })


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'})


@app.route('/status')
def tdx_status():
    """Check TDX availability via the proxy."""
    try:
        response = requests.get(f'{TDX_PROXY_URL}/status', timeout=10)
        return jsonify({
            'tdx_proxy_url': TDX_PROXY_URL,
            'tdx_status': response.json()
        })
    except requests.RequestException as e:
        return jsonify({
            'tdx_proxy_url': TDX_PROXY_URL,
            'error': str(e)
        }), 503


@app.route('/attest')
def attest():
    """Get TDX attestation quote with measurements."""
    try:
        # Get quote from TDX proxy
        response = requests.get(f'{TDX_PROXY_URL}/quote', timeout=60)

        if response.status_code != 200:
            return jsonify({
                'error': 'Failed to get TDX quote',
                'status_code': response.status_code
            }), 503

        quote_data = response.json()

        # Return attestation result
        return jsonify({
            'attestation': {
                'measurements': quote_data.get('measurements', {}),
                'quote_size': quote_data.get('quote_size', 0),
                'quote_preview': quote_data.get('quote', '')[:100] + '...',
            },
            'message': 'TDX attestation successful!'
        })

    except requests.RequestException as e:
        return jsonify({
            'error': f'TDX attestation failed: {str(e)}'
        }), 503


@app.route('/attest/custom', methods=['POST'])
def attest_custom():
    """Get TDX attestation quote with custom report data."""
    from flask import request

    try:
        # Get custom report data from request
        data = request.get_json() or {}
        custom_data = data.get('data', 'hello-world-attestation')

        # Encode as base64 (TDX report data is 64 bytes)
        report_data = custom_data.encode('utf-8')[:64].ljust(64, b'\x00')
        report_data_b64 = base64.b64encode(report_data).decode()

        # Get quote with custom report data
        response = requests.post(
            f'{TDX_PROXY_URL}/quote',
            json={'reportData': report_data_b64},
            timeout=60
        )

        if response.status_code != 200:
            return jsonify({
                'error': 'Failed to get TDX quote',
                'status_code': response.status_code
            }), 503

        quote_data = response.json()

        return jsonify({
            'attestation': {
                'measurements': quote_data.get('measurements', {}),
                'quote_size': quote_data.get('quote_size', 0),
                'custom_data': custom_data,
            },
            'message': 'TDX attestation with custom data successful!'
        })

    except requests.RequestException as e:
        return jsonify({
            'error': f'TDX attestation failed: {str(e)}'
        }), 503


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
