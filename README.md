# Kimi K3.1 Pro on Tinfoil

This repository signs a measured deployment of Tinfoil's Kimi K3.1 Pro recipe with native vLLM bearer authentication. It uses the upstream OCI image, serving arguments, eight-GPU allocation, and schema 1 Modelwrap packs for both Kimi K3.1 Pro and DSpark. [Upstream recipe](https://github.com/tinfoilsh/confidential-kimi-k3-1-pro/blob/v0.0.2/tinfoil-config.yml)

Release `v0.0.3` declares required `VLLM_API_KEY` and `METRICS_API_KEY` secrets. Native vLLM authentication protects `/v1/models`, `/v1/chat/completions`, and `/v1/responses` using the configured application bearer. The shim forwards these requests and serves public `/health`. Its shared Tinfoil credential validator is disabled. Public engine `/metrics` and `/tokenize` routes are omitted. Built-in guest metrics use `METRICS_API_KEY`.

The current configuration SHA-256 is `2400260beabc0fe45b1c959a29c1401fbd703d6b233efa7de883eccba29de68b`. Verify the deployment artifact's GitHub/Sigstore signature against this repository and its release tag, then verify the endpoint against the exact release digest. Both weight repositories and immutable revisions appear in the measured configuration. [Attestation verification](https://docs.tinfoil.sh/sdk/cli-sdk)

The earlier `v0.0.2` release preserves the original upstream configuration byte for byte. Its configuration SHA-256 is `4766e0aba2c4530cacf3081b29d96fac937354e4c6b6966634d84e5f3457bd7a`, and its deployment artifact SHA-256 is `8cf7c851336ced05cef347eef3055d3380f86e798b00137fec06033d75ba7ae9`. [Baseline release](https://github.com/MaplePrivacyLabs/inference-kimi-k3-1-pro/releases/tag/v0.0.2)
