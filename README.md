# Stock Kimi K3.1 Pro on Tinfoil

This repository signs a byte-for-byte copy of Tinfoil's v0.0.2 deployment configuration for Maple's 8×B300 staging run. It uses the upstream OCI image, the original serving arguments and shim, and Tinfoil's schema 1 Modelwrap packs for both Kimi K3.1 Pro and DSpark. [Tinfoil v0.0.2](https://github.com/tinfoilsh/confidential-kimi-k3-1-pro/releases/tag/v0.0.2)

The configuration SHA-256 is `4766e0aba2c4530cacf3081b29d96fac937354e4c6b6966634d84e5f3457bd7a`. The expected deployment artifact SHA-256 is `8cf7c851336ced05cef347eef3055d3380f86e798b00137fec06033d75ba7ae9`. Verify the artifact signature against the Maple repository and release tag, then verify the running endpoint against that exact release. [Tinfoil attestation verification](https://docs.tinfoil.sh/sdk/cli-sdk)

The original shim exposes `/health` and `/v1/models` and uses standard Tinfoil authentication for generation and tokenization. Its `/metrics` route uses Tinfoil admin authentication. Both weight repositories and immutable revisions appear in the measured configuration. [Stock configuration](https://github.com/tinfoilsh/confidential-kimi-k3-1-pro/blob/v0.0.2/tinfoil-config.yml)
