"""Check that the configuration is stock Kimi K3.1 Pro plus the listed differences."""

import argparse
import hashlib
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent
# This repository's v0.0.3: Tinfoil's v0.0.2 recipe with native vLLM bearer
# authentication. Tinfoil's shared Kimi K3.1 Pro fleet runs the same recipe.
STOCK_CONFIG_SHA256 = "2400260beabc0fe45b1c959a29c1401fbd703d6b233efa7de883eccba29de68b"
IMAGE = "ghcr.io/mapleprivacylabs/inference-kimi-k3-1-pro"
STOCK_IMAGE = "ghcr.io/tinfoilsh/confidential-kimi-k31-pro@sha256:0a81868bb275945f23e0e71d53524dd9a416bfcde3acb14903af0c2139495bc0"
# The source names the image without a digest. The release workflow builds the
# image and writes the pinned line into the tagged configuration.
IMAGE_TEMPLATE_LINE = f'  image: "{IMAGE}:build-required" # source template; the release workflow pins the built digest\n'
IMAGE_PINNED_LINE = rf'  image: "{re.escape(IMAGE)}@sha256:[0-9a-f]{{64}}" # v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\n'
# Every difference from stock (see CHANGES.md). Each entry is (text in stock,
# text in this configuration). Undoing every entry must give back the stock
# configuration exactly, so the configuration cannot differ from stock in any
# way that is not listed here. The model weights, their packs and the served
# model name are not in this list: they are stock.
EDITS = [
    ("cpus: 32\n", "cpus: 120\n"),
    ('"num_speculative_tokens":5', '"num_speculative_tokens":3'),
    (f'  image: "{STOCK_IMAGE}" # v0.0.2\n', IMAGE_TEMPLATE_LINE),
    ("  - --port\n  - '8001'\n", "  - --middleware\n  - maple_metrics_auth.MetricsAuthMiddleware\n  - --port\n  - '8001'\n"),
    ("  - /health\n", "  - /health\n  - /metrics\n"),
]


def check(config, require_pinned_image=False):
    """Raise ValueError unless `config` is stock plus exactly the listed differences."""
    # A tagged release carries the pinned image; the source carries the template line.
    config, pinned = re.subn(IMAGE_PINNED_LINE, lambda _: IMAGE_TEMPLATE_LINE, config)
    if pinned > 1 or (require_pinned_image and pinned != 1):
        raise ValueError("Expected exactly one pinned image line for this repository's image")
    stock = config
    for stock_text, our_text in EDITS:
        if stock.count(our_text) != 1:
            raise ValueError(f"Expected one listed difference matching {our_text!r}")
        stock = stock.replace(our_text, stock_text)
    if hashlib.sha256(stock.encode("utf-8")).hexdigest() != STOCK_CONFIG_SHA256:
        raise ValueError("Configuration differs from stock v0.0.3 outside the listed differences")


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
