"""Entry point for python -m gateway."""

import os
from gateway.server import run_gateway

port = int(os.environ.get("OCF_GATEWAY_PORT", "9400"))
run_gateway(port=port)