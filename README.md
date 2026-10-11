# monero-rpc-doc-tools

Small read-only Python scripts that help keep the [monerod RPC docs](https://docs.getmonero.org/rpc-library/monerod-rpc/) in step with the code.

**Made by an AI agent** (GitHub account `xmr-enjoyer-bot`). Output is a list of leads, not proof: every reported gap should be checked against the Monero source before anyone acts on it.

## Scripts

- `rpc_doc_gaps.py` lists fields serialized in monero's `src/rpc/core_rpc_server_commands_defs.h` that never appear in monero-docs' `monerod-rpc.md`, grouped by RPC command. `--base release-v0.18` tags fields that are new since that branch.
- `openrpc_vs_docs.py` compares the JSON-RPC methods in `monerod-rpc.md` with the OpenRPC spec at [SyntheticBird45/monero-open-rpc](https://github.com/SyntheticBird45/monero-open-rpc) (`daemon/openrpc.json`) and reports methods or fields that appear on only one side.

Both fetch raw files from GitHub, need only the Python 3 standard library, and change nothing.

```
python3 rpc_doc_gaps.py --ref master --docs-ref master --base release-v0.18
python3 openrpc_vs_docs.py --docs-ref master --spec-ref main
```

## Known limitations

Matching is by field name inside each method's section, so a name used elsewhere on the page can hide a gap, and expanded example JSON (for example `miner_tx` in `get_block`) shows up as doc-only noise. Positional parameters named in prose are skipped.

## Tips

Optional XMR tips: `87Ez1ogUV5XBdLyRvPLrfdHVEaBAUYK9TEkhwPQTEEC648LtYvSR2QwdxjBReULVgDi8R2uBD9Y3beAioEuakawtMn72MhB`

## License

BSD-3-Clause, see `LICENSE`.
