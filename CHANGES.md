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

Maple's five differences below are unchanged.

Measured on the dedicated node (v0.2.0, November 20, 2026): it starts in the
usual time; vLLM reports a cache of 14.3 million tokens (1,035 blocks, 16,384
attention tokens per block) against 2.4 million; sixty 100,000-token prompts
all stayed cached, where v0.1.0 kept twenty-three; short-prompt decode is 8 to
13% slower (122-128 tokens/s for one request, 1,450-1,465 at 32, against
140-148 and 1,563-1,605); reading a cold 100,000-token prompt takes the same
five seconds.

### Further changes under evaluation

| Release | Change | Why |
|---|---|---|
| v0.2.1 | `--prefill-schedule-interval 8` | Under a realistic long-context load, streams slow down most when other requests' prompt chunks share their engine step. This admits prefill on one step in eight and leaves the others to decode alone. vLLM's own B300 presets for agentic load use the same value. |
| v0.2.2 | Compiled graphs for engine steps of up to 4,096 tokens (`cudagraph_capture_sizes` extended from 192 to 4,096) | With the cache working, most prompt chunks are a few thousand new tokens. Today any step carrying more than 192 tokens runs without a compiled graph, and every decoding request waits for it. vLLM's B300 preset for 12 to 24 concurrent agents does the same. Costs start-up time and some cache memory. |
| v0.2.3 | `rejection_sample_method` `block` instead of `standard`; no `--kernel-config`, so vLLM picks the sparse-attention kernel itself | Block verification accepts more draft tokens per step without changing the output distribution; vLLM's B300 presets use it. With the cache split across GPUs vLLM's own default is a newer attention kernel than the one Tinfoil's recipe pins; this measures it on this host. A long-context retrieval check is run on both to confirm answers do not change. |
| v0.2.4 | `--max-num-batched-tokens 4096` instead of 16,384; `--prefill-schedule-interval` removed | v0.2.2's compiled graphs cover steps of up to 4,096 tokens, but a cold prompt is still read in 16,384-token steps that run eagerly while every stream waits. Capping the step at the largest compiled size makes every step a graph replay and returns the memory the larger step reserved. v0.2.1's interval of 8 gained 3 to 6% in stream speed for half a second of first-token delay and is dropped here, because with small steps it would slow cold prompts too much. |
| v0.2.5 | `--max-num-seqs 48` instead of 32 | At overload the node sits at its 32-request cap with more requests waiting for a slot. This measures whether total output keeps rising with more requests in the batch, and what it costs each stream and the cache, since every running request holds a fixed share of the cache pool. |

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
| v0.2.1 | `--prefill-schedule-interval 8`. Under evaluation. |
| v0.2.2 | Compiled graphs for steps of up to 4,096 tokens. Under evaluation. |
| v0.2.3 | Block verification of draft tokens; default sparse-attention kernel. Under evaluation. |
| v0.2.4 | Engine step capped at 4,096 tokens; prefill interval removed. Under evaluation. |
| v0.2.5 | Up to 48 concurrent requests. Under evaluation. |
