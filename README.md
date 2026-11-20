# Kimi K3.1 Pro on Tinfoil

This repository signs a measured deployment of Tinfoil's Kimi K3.1 Pro recipe for Maple's dedicated node. The weights are stock: `moonshotai/Kimi-K3.1-Pro` and the Inferact DSpark draft model, each pinned to an immutable revision and a schema 1 Modelwrap pack, served under the model name `kimi-k3-1-pro`. Release v0.1.0 follows Tinfoil's recipe v0.0.2, which their shared fleet runs; v0.2.0 adds the changes of their recipe v0.0.3 and is under evaluation. [Upstream recipe](https://github.com/tinfoilsh/confidential-kimi-k3-1-pro/blob/v0.0.2/tinfoil-config.yml)

From v0.1.0 the configuration differs from stock in five listed ways, none of which touch the weights: more vCPUs, three draft tokens instead of five, and vLLM's `/metrics` served behind the Maple metrics key by an image this repository builds. [CHANGES.md](CHANGES.md) gives each difference and its reason.

## Authentication

Releases declare required `VLLM_API_KEY` and `METRICS_API_KEY` secrets. Native vLLM authentication protects `/v1/models`, `/v1/chat/completions` and `/v1/responses` with the application bearer. The shim forwards these requests and serves public `/health`. Its shared Tinfoil credential validator is disabled. `/metrics` and the built-in guest metrics require `METRICS_API_KEY`. `/tokenize` and the Anthropic Messages paths are not exposed.

## The serving image

The [Dockerfile](Dockerfile) starts from the exact image the stock configuration pins and adds [`maple_metrics_auth.py`](maple_metrics_auth.py) through [`scripts/install_metrics_auth.py`](scripts/install_metrics_auth.py). The installer checks the vLLM version and the three places in vLLM's source the guard depends on, and fails the build if any has changed. Tests in `tests/` cover the guard and check that the Dockerfile, the configuration and the guard agree.

## Prepare and verify a release

The source names the image without a digest. The release workflow builds the image, writes its digest into the configuration on a release-only commit, tags that commit and measures it. `python3 check_config.py` checks the configuration on the default branch and again, with `--require-pinned-image`, at the release tag: undoing the listed differences must give back the stock configuration exactly.

To verify a release, read `tinfoil-config.yml` at the published tag and check both weight revisions, their Modelwrap tuples, the image digest and the paths passed to `--model` and `--speculative-config`. Then verify the deployment artifact's GitHub/Sigstore signature against this repository and its release tag, and verify the endpoint against the exact release digest. [Attestation verification](https://docs.tinfoil.sh/sdk/cli-sdk)

## Earlier releases

`v0.0.3` is the stock recipe with native bearer authentication; its configuration SHA-256 is `2400260beabc0fe45b1c959a29c1401fbd703d6b233efa7de883eccba29de68b`. `v0.0.2` preserves the original upstream configuration byte for byte: configuration SHA-256 `4766e0aba2c4530cacf3081b29d96fac937354e4c6b6966634d84e5f3457bd7a`, deployment artifact SHA-256 `8cf7c851336ced05cef347eef3055d3380f86e798b00137fec06033d75ba7ae9`. [Baseline release](https://github.com/MaplePrivacyLabs/inference-kimi-k3-1-pro/releases/tag/v0.0.2)
