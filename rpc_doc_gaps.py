#!/usr/bin/env python3
"""rpc_doc_gaps.py - flag monerod RPC fields that appear in monero's
core_rpc_server_commands_defs.h but are never mentioned in monero-docs'
monerod-rpc.md (possibly undocumented). Fields are grouped by the RPC command
struct they belong to. Read-only; fetches raw files from GitHub.
Made by an AI agent.

Usage: python3 rpc_doc_gaps.py [--ref master] [--docs-ref master]
                               [--base release-v0.18] [--all]
  --base REF   also fetch REF and tag each field NEW if it is absent there
               (i.e. added since that release branch).
  --all        include helper/base structs (rpc_*_base etc.) normally skipped.
"""
import argparse, re, urllib.request
from collections import defaultdict

RAW = "https://raw.githubusercontent.com/monero-project"
SKIP_STRUCT = re.compile(r'(_base$|^rpc_)')
SKIP_FIELD = re.compile(r'^rpc_\w*_base$')  # KV_SERIALIZE_PARENT(...) of base structs

def get(url):
    return urllib.request.urlopen(url, timeout=30).read().decode()

def fields_by_struct(hdr):
    """Map field -> set of enclosing 'struct' paths, e.g. COMMAND_RPC_GET_VERSION.response_t."""
    out, stack, depth = defaultdict(set), [], 0
    for line in hdr.splitlines():
        code = line.split('//')[0]
        m = re.search(r'\bstruct\s+(\w+)', code)
        if m and not code.rstrip().endswith(';'):
            stack.append((m.group(1), depth))
        for f in re.findall(r'KV_SERIALIZE(?:_[A-Z_]+)?\(\s*([a-z_][a-z0-9_]*)', code):
            out[f].add('.'.join(s for s, _ in stack) or '?')
        depth += code.count('{') - code.count('}')
        while stack and depth <= stack[-1][1] and '}' in code:
            stack.pop()
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ref', default='master')
    ap.add_argument('--docs-ref', default='master')
    ap.add_argument('--base')
    ap.add_argument('--all', action='store_true')
    a = ap.parse_args()
    hpath = '/src/rpc/core_rpc_server_commands_defs.h'
    hdr = get(f"{RAW}/monero/{a.ref}{hpath}")
    doc = get(f"{RAW}/monero-docs/{a.docs_ref}/docs/en/rpc-library/monerod-rpc.md")
    fields = fields_by_struct(hdr)
    base = set(fields_by_struct(get(f"{RAW}/monero/{a.base}{hpath}"))) if a.base else None
    words = {w.strip('_') for w in re.findall(r'[a-z_][a-z0-9_]*', doc)}  # docs use _italic_ names
    by_cmd = defaultdict(list)
    for f, owners in fields.items():
        if f in words or (not a.all and SKIP_FIELD.match(f)):
            continue
        for o in owners:
            top = o.split('.')[0]
            if not a.all and (SKIP_STRUCT.search(top) or SKIP_STRUCT.search(o.split('.')[-1])):
                continue
            tag = ' [NEW since %s]' % a.base if base is not None and f not in base else ''
            by_cmd[top].append(f"{o.split('.', 1)[-1] if '.' in o else ''}.{f}{tag}".lstrip('.'))
    n = sum(len(v) for v in by_cmd.values())
    print(f"# monero {a.ref} vs monero-docs {a.docs_ref}: {n} undocumented field uses in {len(by_cmd)} structs")
    for cmd in sorted(by_cmd):
        print(cmd)
        for x in sorted(set(by_cmd[cmd])):
            print('   ', x)

if __name__ == '__main__':
    main()
