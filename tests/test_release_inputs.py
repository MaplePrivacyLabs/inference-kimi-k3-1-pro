"""The image, the measured configuration and the metrics guard must agree with each other."""

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import check_config  # noqa: E402

CONFIG = (ROOT / "tinfoil-config.yml").read_text()
PINNED = CONFIG.replace(
    check_config.IMAGE_TEMPLATE_LINE,
    f'  image: "{check_config.IMAGE}@sha256:{"a" * 64}" # v0.1.0\n',
)


def block(text, key):
    """The list items under a top-level-or-nested `key:` line, in order."""
    match = re.search(rf"^( *){re.escape(key)}:\n((?:\1 *- .*\n)+)", text, re.MULTILINE)
    if match is None:
        raise AssertionError(f"No list under {key!r}")
    return [line.strip()[2:] for line in match.group(2).splitlines()]


class ReleaseInputs(unittest.TestCase):
    def test_image_is_built_from_the_stock_image(self):
        dockerfile = (ROOT / "Dockerfile").read_text()
        self.assertEqual(re.findall(r"^FROM (\S+)$", dockerfile, re.MULTILINE), [check_config.STOCK_IMAGE])

    def test_image_adds_only_the_guard(self):
        dockerfile = (ROOT / "Dockerfile").read_text()
        instructions = [line.split()[0] for line in dockerfile.splitlines() if line and line[0].isalpha()]
        self.assertEqual(instructions, ["FROM", "COPY", "RUN"])
        ignore = (ROOT / ".dockerignore").read_text().split()
        self.assertEqual(ignore, ["**", "!Dockerfile", "!maple_metrics_auth.py", "!scripts/", "!scripts/install_metrics_auth.py"])

    def test_source_names_exactly_one_unpinned_image_of_ours(self):
        self.assertEqual(re.findall(r'^ *image: "([^"]+)"', CONFIG, re.MULTILINE), [f"{check_config.IMAGE}:build-required"])

    def test_public_paths(self):
        self.assertEqual(
            block(CONFIG, "  paths"),
            ["/v1/chat/completions", "/v1/models", "/v1/responses", "/health", "/metrics"],
        )

    def test_metrics_is_public_only_with_the_guard_and_its_key(self):
        command = block(CONFIG, "  command")
        index = command.index("--middleware")
        self.assertEqual(command[index + 1], "maple_metrics_auth.MetricsAuthMiddleware")
        self.assertEqual(command.count("--middleware"), 1)
        self.assertEqual(block(CONFIG, "  secrets"), ["VLLM_API_KEY", "METRICS_API_KEY"])
        # The guard is Python middleware, so the Python API server must stay selected.
        self.assertIn("  - VLLM_USE_RUST_FRONTEND: '0'\n", CONFIG)

    def test_weights_and_served_name_are_stock(self):
        self.assertEqual(
            re.findall(r"^  repo: (\S+)$", CONFIG, re.MULTILINE),
            [
                "moonshotai/Kimi-K3.1-Pro@6d0a0202956796543364d666ab19c6ad1a494ee1",
                "Inferact/Kimi-K3.1-Pro-DSpark-preview@5e654fbe920278f228a89519b06b2680aa56480f",
            ],
        )
        command = block(CONFIG, "  command")
        self.assertEqual(command[command.index("--served-model-name") + 1], "kimi-k3-1-pro")
        self.assertEqual(command.count("--served-model-name"), 1)

    def test_installer_expects_the_stock_vllm_build(self):
        installer = (ROOT / "scripts" / "install_metrics_auth.py").read_text()
        self.assertIn('EXPECTED_VLLM = "0.1.dev24216+g266e88c05"', installer)


class ConfigCheck(unittest.TestCase):
    def test_source_and_pinned_configurations_pass(self):
        check_config.check(CONFIG)
        check_config.check(PINNED, require_pinned_image=True)

    def test_source_fails_when_a_pinned_image_is_required(self):
        with self.assertRaises(ValueError):
            check_config.check(CONFIG, require_pinned_image=True)

    def test_an_image_from_elsewhere_is_refused(self):
        other = PINNED.replace(check_config.IMAGE, "ghcr.io/example/other")
        with self.assertRaises(ValueError):
            check_config.check(other, require_pinned_image=True)

    def test_any_unlisted_difference_is_refused(self):
        changes = [
            ("  - '1048576'\n", "  - '262144'\n"),
            ("  - '8'\n  - --dcp-comm-backend\n  - a2a\n", "  - '8'\n  - --dcp-comm-backend\n  - ag_rs\n"),
            ("  - kimi-k3-1-pro\n  - --tensor", "  - kimi-k3-1-pro-other\n  - --tensor"),
            ("8d9c355a94e60f43", "0e6d901b33b7a141"),
            ("  - /metrics\n", "  - /metrics\n  - /tokenize\n"),
            ("  - /health\n  - /metrics\n", "  - /health\n"),
            ("gpus: 8\n", "gpus: 4\n"),
        ]
        for before, after in changes:
            with self.subTest(after=after):
                self.assertIn(before, CONFIG)
                with self.assertRaises(ValueError):
                    check_config.check(CONFIG.replace(before, after))

    def test_undoing_every_listed_difference_gives_stock(self):
        # Each listed difference is present exactly once, so none is dead.
        for _, ours in check_config.EDITS + check_config.UPSTREAM_V003_EDITS[1:]:
            self.assertEqual(CONFIG.count(ours), 1, ours)


if __name__ == "__main__":
    unittest.main()
