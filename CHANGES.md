# Differences from stock

The model weights, their Modelwrap packs, the DSpark draft model and the served
model name `kimi-k3-1-pro` are Tinfoil's stock Kimi K3.1 Pro, unchanged.

[`check_config.py`](check_config.py) lists every difference from stock and
refuses a configuration that differs in any other way. "Stock" is this
repository's v0.0.3: Tinfoil's v0.0.2 recipe with native vLLM bearer
authentication. `UPSTREAM_V003_EDITS` holds Tinfoil's own changes from their
recipe v0.0.2 to v0.0.3; `EDITS` holds Maple's.

## v0.2.0: Tinfoil's v0.0.3 recipe (under evaluation)

Release v0.1.0 is the qualified configuration. On the dedicated node its
prefix cache holds about 2.4 million tokens (1,179 blocks of 2,048), shared
between running requests and retained conversations. That is roughly twenty
warm 100,000-token conversations, and load tests showed cache hits collapsing
beyond it. v0.2.0 adds the changes Tinfoil made in their recipe v0.0.3
("expand long-context serving capacity") to see what they do on this host:

| Tinfoil v0.0.2 | Tinfoil v0.0.3 | What it is for |
|---|---|---|
| `--decode-context-parallel-size 1` | `8`, with `--dcp-comm-backend a2a` | The attention cache is split across the eight GPUs by token position instead of being repeated on each, so one block covers eight times the tokens. |
| image v0.0.2 | image v0.0.3 | Same vLLM build with a small warm-up change. |
| `expandable_segments:True` | `expandable_segments:False`, also as `PYTORCH_ALLOC_CONF` | Allocator setting Tinfoil ships with the change. |
| no `--kernel-config` | `{"flashinfer_sparse_mla_kernel":"trtllm"}` | Keeps the attention kernel v0.0.2 uses. |
| `--max-model-len 262144` | `1048576` | The length the change was made to support. |
| no `--prefix-match-unit` | `128` | Cache hits can land on a 128-token boundary instead of a whole block. |

Maple's five differences below are unchanged. Whether this configuration is
kept depends on measurements that have not been made yet: start-up on this
host, cache capacity, and decode speed with the extra GPU-to-GPU traffic.

## Maple's differences (v0.1.0 onwards)

| Difference from stock | Why |
|---|---|
| `cpus` 120 instead of 32 | The host is already paid for. Measured throughput is unchanged up to 32 concurrent requests. The platform accepts 2, 4, 8, 16, 32, 56, 64, 120 or 128 vCPUs. |
| Three DSpark draft tokens instead of five | About 15% more output at 32 concurrent requests: 1,568-1,612 tokens/s against 1,358-1,378. With five, the fourth and fifth draft tokens were accepted 13% and 7% of the time while every step carried a third more rows. Speculative decoding with rejection sampling does not change the model's output distribution. |
| Image built by this repository from Tinfoil's image | The [Dockerfile](Dockerfile) adds one file, [`maple_metrics_auth.py`](maple_metrics_auth.py), and changes nothing else. The build fails if the base image's vLLM is not the build the guard was written against. |
| `--middleware maple_metrics_auth.MetricsAuthMiddleware` | Loads the guard. It requires the `METRICS_API_KEY` bearer on every path under `/metrics` and passes all other requests through untouched. |
| `/metrics` in the shim paths | vLLM's Prometheus metrics (queue, cache, latency, token and speculative-decoding counters) become readable with the metrics key. Without the guard this path would be open: vLLM's own bearer check does not cover it. |

The same key already protects the shim's own `/.well-known/tinfoil-metrics` and
`/.well-known/metrics`. Metrics are counters and histograms; they contain no
request content.

The vCPU and draft-token measurements were taken on this host class (eight
B300 GPUs) in November 2026 with a fine-tuned checkpoint of the same
architecture and size, served by
[inference-penclaw](https://github.com/MaplePrivacyLabs/inference-penclaw)
with this same configuration. They have not yet been repeated on the stock
weights.

## Release history

| Release | Change from the previous release |
|---|---|
| v0.0.2 | Tinfoil's v0.0.2 configuration, byte for byte. |
| v0.0.3 | Native vLLM bearer authentication with `VLLM_API_KEY`; `METRICS_API_KEY` for the built-in guest metrics; public engine `/metrics` and `/tokenize` removed from the shim paths. |
| v0.1.0 | Maple's five differences in the table above. |
| v0.2.0 | Tinfoil's v0.0.3 recipe changes, listed at the top. Under evaluation. |
