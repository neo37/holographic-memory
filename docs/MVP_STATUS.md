# MVP Status — Reference Implementation

> **Note on language:** the product docs describe a **Go** edition (planned distribution
> target). The **reference implementation** in this repo is **Python** (`src/holographic_memory/`)
> — chosen for fast iteration and because the SDM engine maps cleanly onto NumPy.

## What works today (v0.1)

- ✅ **MCP server over stdio** (newline-delimited JSON-RPC 2.0), standard-library only.
  `initialize`, `tools/list`, `tools/call`, `ping`, notifications.
- ✅ **Real Kanerva SDM engine** (`sdm.py`): random hard locations, k-nearest activation,
  superposed writes, majority-rule (`sign(sum)`) reads.
- ✅ **All 4 tools**: `store_holographic_snapshot`, `recall_by_association`,
  `interference_analysis`, `consolidate_and_prune`.
- ✅ **Persistence**: addresses / counters / vectors (`.npy`) + snapshot metadata (JSON).
- ✅ **License gate**: free `MEMORY_MODE=LOCAL`; paid modes validate against Lemon Squeezy
  (24h cache).

Verified end-to-end: with shared vocabulary, recall similarity is sharp (e.g. `"python
backend preference"` → `0.83` for the Python/Go fact vs `~0.5` noise floor for unrelated
memories); interference correctly flags a contradicting location.

## Known limitation — encoder is lexical, not yet semantic

The current encoder (`encoder.py`) is **hyperdimensional bundling of token vectors**, so
association works through **shared vocabulary**. A query that shares no words with a stored
fact (e.g. `"what language for this script?"` vs `"dislikes Python"`) lands near the noise
floor.

### Next milestone (v0.2) — semantic encoding

Make the encoder pluggable and add an **embedding backend** (e.g. a local sentence-embedding
model) whose vector is binarized into the hypervector. That is what delivers true
paraphrase-level association — the headline demo. The SDM layer above it stays unchanged.

## Run it

```bash
pip install -r requirements.txt        # numpy
cd src && python -m holographic_memory  # speaks MCP on stdio
```

Config via env: `MEMORY_MODE` (LOCAL), `MEMORY_STORE_PATH` (~/.holographic-memory),
`MEMORY_DIM` (10000), `MEMORY_LICENSE_KEY` (paid modes only).
