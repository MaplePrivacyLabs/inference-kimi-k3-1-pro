"""Check that the configuration is stock Kimi K3.1 Pro plus the listed differences: Tinfoil's v0.0.3 changes and Maple's."""

import argparse
import hashlib
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent
# This repository's v0.0.3: Tinfoil's v0.0.2 recipe with native vLLM bearer
# authentication. Every later difference is listed below, so undoing all of
# them must give back exactly this configuration.
STOCK_CONFIG_SHA256 = "2400260beabc0fe45b1c959a29c1401fbd703d6b233efa7de883eccba29de68b"
IMAGE = "ghcr.io/mapleprivacylabs/inference-kimi-k3-1-pro"
STOCK_V002_IMAGE = "ghcr.io/tinfoilsh/confidential-kimi-k31-pro@sha256:0a81868bb275945f23e0e71d53524dd9a416bfcde3acb14903af0c2139495bc0"
# The image this repository builds from: Tinfoil's v0.0.3 Kimi K3.1 Pro image.
STOCK_IMAGE = "ghcr.io/tinfoilsh/confidential-kimi-k31-pro@sha256:a74bdc3660cd5aaca97528e8e07930e7117b9f0d0cdb6dbde84745d02a09ffde"
# The source names the image without a digest. The release workflow builds the
# image and writes the pinned line into the tagged configuration.
IMAGE_TEMPLATE_LINE = f'  image: "{IMAGE}:build-required" # source template; the release workflow pins the built digest\n'
IMAGE_PINNED_LINE = rf'  image: "{re.escape(IMAGE)}@sha256:[0-9a-f]{{64}}" # v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\n'
# Tinfoil's own changes from recipe v0.0.2 to v0.0.3 ("expand long-context
# serving capacity"), each as (text in v0.0.2, text in v0.0.3).
UPSTREAM_V003_EDITS = [
    (f'  image: "{STOCK_V002_IMAGE}" # v0.0.2\n', f'  image: "{STOCK_IMAGE}" # v0.0.3\n'),
    ("  - PYTORCH_CUDA_ALLOC_CONF: expandable_segments:True\n",
     "  - PYTORCH_CUDA_ALLOC_CONF: expandable_segments:False\n  - PYTORCH_ALLOC_CONF: expandable_segments:False\n"),
    ("  - --decode-context-parallel-size\n  - '1'\n", "  - --decode-context-parallel-size\n  - '8'\n  - --dcp-comm-backend\n  - a2a\n"),
    ("  - --disable-custom-all-reduce\n",
     "  - --kernel-config\n  - '{\"flashinfer_sparse_mla_kernel\":\"trtllm\"}'\n  - --disable-custom-all-reduce\n"),
    ("  - --max-model-len\n  - '262144'\n", "  - --max-model-len\n  - '1048576'\n"),
    ("  - --enable-prefix-caching\n", "  - --enable-prefix-caching\n  - --prefix-match-unit\n  - '128'\n"),
]
# Maple's differences from Tinfoil's v0.0.3 recipe (see CHANGES.md). Each entry
# is (text in Tinfoil's recipe, text in this configuration). Undoing these and
# then Tinfoil's own v0.0.3 changes must give back the stock configuration
# exactly, so the configuration cannot differ in any way that is not listed
# here. The model weights, their packs and the served model name are not in
# either list: they are stock.
EDITS = [
    ("cpus: 32\n", "cpus: 120\n"),
    ('"num_speculative_tokens":5', '"num_speculative_tokens":3'),
    (f'  image: "{STOCK_IMAGE}" # v0.0.3\n', IMAGE_TEMPLATE_LINE),
    ("  - --port\n  - '8001'\n", "  - --middleware\n  - maple_metrics_auth.MetricsAuthMiddleware\n  - --port\n  - '8001'\n"),
    ("  - /health\n", "  - /health\n  - /metrics\n"),
    # v0.2.4, under evaluation: at most 4,096 tokens per engine step, the largest
    # size with a compiled graph, so no step runs eagerly while other requests
    # wait. Replaces v0.2.1's --prefill-schedule-interval 8, which gained little.
    ("  - --max-num-batched-tokens\n  - '16384'\n", "  - --max-num-batched-tokens\n  - '4096'\n"),
    # v0.2.5, under evaluation: up to 48 requests decoding at once instead of 32.
    ("  - --max-num-seqs\n  - '32'\n", "  - --max-num-seqs\n  - '48'\n"),
    # v0.2.2, under evaluation: compiled graphs for engine steps of up to 4,096
    # tokens, so steps that carry a short prompt chunk beside the decoding
    # requests replay a graph instead of running eagerly.
    (',180,186,192],"max_cudagraph_capture_size":192}\'',
     ',180,186,192,224,256,320,384,448,512,640,768,1024,1280,1536,1792,2048,2560,3072,3584,4096],"max_cudagraph_capture_size":4096}\''),
    # v0.2.3, under evaluation: block verification of draft tokens, and vLLM's
    # default choice of sparse-attention kernel instead of the one Tinfoil pins.
    ('"rejection_sample_method":"standard"', '"rejection_sample_method":"block"'),
    ("  - --kernel-config\n  - '{\"flashinfer_sparse_mla_kernel\":\"trtllm\"}'\n  - --disable-custom-all-reduce\n",
     "  - --disable-custom-all-reduce\n"),
]


def check(config, require_pinned_image=False):
    """Raise ValueError unless `config` is stock plus exactly the listed differences."""
    # A tagged release carries the pinned image; the source carries the template line.
    config, pinned = re.subn(IMAGE_PINNED_LINE, lambda _: IMAGE_TEMPLATE_LINE, config)
    if pinned > 1 or (require_pinned_image and pinned != 1):
        raise ValueError("Expected exactly one pinned image line for this repository's image")
    stock = config
    for before, after in EDITS + UPSTREAM_V003_EDITS:
        if stock.count(after) != 1:
            raise ValueError(f"Expected one listed difference matching {after!r}")
        stock = stock.replace(after, before)
    if hashlib.sha256(stock.encode("utf-8")).hexdigest() != STOCK_CONFIG_SHA256:
        raise ValueError("Configuration differs from stock outside the listed differences")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "tinfoil-config.yml")
    parser.add_argument("--require-pinned-image", action="store_true", help="The configuration must pin a built image digest")
    args = parser.parse_args()
    try:
        check(args.config.read_bytes().decode("utf-8"), args.require_pinned_image)
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
