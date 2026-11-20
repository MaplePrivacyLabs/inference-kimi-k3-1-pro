# syntax=docker/dockerfile:1.6
# Tinfoil's qualified Kimi K3.1 Pro runtime, unchanged: same vLLM build, kernels,
# confidential-computing settings and entrypoint. The only addition is one file,
# a guard that requires the Maple metrics key on vLLM's /metrics.
FROM ghcr.io/tinfoilsh/confidential-kimi-k31-pro@sha256:a74bdc3660cd5aaca97528e8e07930e7117b9f0d0cdb6dbde84745d02a09ffde

COPY maple_metrics_auth.py scripts/install_metrics_auth.py /tmp/
RUN python3 -B /tmp/install_metrics_auth.py && \
    rm /tmp/install_metrics_auth.py /tmp/maple_metrics_auth.py
