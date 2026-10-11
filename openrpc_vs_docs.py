#!/usr/bin/env python3
"""openrpc_vs_docs.py - compare monero-docs' monerod-rpc.md (JSON-RPC section)
with the OpenRPC spec at SyntheticBird45/monero-open-rpc (daemon/openrpc.json).
For every JSON-RPC method it reports:
  * methods documented but missing from the spec, and vice versa
  * input/output field names present in the spec but not in that method's docs
  * field names in the docs section but not in the spec (doc-only)
Field matching is by name within the method's section/schema (nested fields
flattened). Read-only; fetches raw files from GitHub. Made by an AI agent.

Usage: python3 openrpc_vs_docs.py [--docs-ref master] [--spec-ref main]
                                  [--spec FILE] [--docs FILE] [--json]
"""
import argparse, json, re, sys, urllib.request

DOCS = "https://raw.githubusercontent.com/monero-project/monero-docs/{}/docs/en/rpc-library/monerod-rpc.md"
SPEC = "https://raw.githubusercontent.com/SyntheticBird45/monero-open-rpc/{}/daemon/openrpc.json"
IGNORE = {'id', 'jsonrpc', 'result', 'method', 'params'}

def get(url):
    return urllib.request.urlopen(url, timeout=30).read().decode()

def deref(spec, node, seen=()):
    if isinstance(node, dict) and '$ref' in node:
        ref = node['$ref']
        if ref in seen:
            return {}
        cur = spec
        for part in ref.lstrip('#/').split('/'):
            cur = cur[part]
        merged = dict(cur); merged.update({k: v for k, v in node.items() if k != '$ref'})
        return deref(spec, merged, seen + (ref,))
    return node

def schema_fields(spec, node, seen=()):
    node = deref(spec, node, seen)
    out = set()
    if not isinstance(node, dict):
        return out
    for k, v in (node.get('properties') or {}).items():
        out.add(k); out |= schema_fields(spec, v, seen)
    for key in ('items', 'additionalProperties'):
        if isinstance(node.get(key), dict):
            out |= schema_fields(spec, node[key], seen)
    for key in ('allOf', 'anyOf', 'oneOf'):
        for sub in node.get(key) or []:
            out |= schema_fields(spec, sub, seen)
    return out

def spec_methods(spec):
    res = {}
    for m in spec['methods']:
        ins = set()
        for p in m.get('params', []):
            p = deref(spec, p)
            ins.add(p.get('name', '')); ins |= schema_fields(spec, p.get('schema', {}))
        outs = schema_fields(spec, (m.get('result') or {}).get('schema', {}))
        # positional params (e.g. on_get_block_hash) carry prose names; skip those
        res[m['name']] = ({i for i in ins if re.fullmatch(r'[a-z_][a-z0-9_]*', i)}, outs)
    return res

def doc_methods(doc):
    """JSON-RPC sections only: '### **name**' headings before 'Other Daemon RPC Calls'."""
    body = doc.split('## Other Daemon RPC Calls')[0]
    parts = re.split(r'^### \*\*([a-z_]+)\*\*\s*$', body, flags=re.M)
    res = {}
    for name, text in zip(parts[1::2], parts[2::2]):
        listed = {w.strip('_') for w in re.findall(r'^\s*[-*]\s+\*?_?([a-z][a-z0-9_]*?)_?\*?\s+-', text, flags=re.M)}
        mentioned = {w.strip('_') for w in re.findall(r'[a-z_][a-z0-9_]*', text)}
        res[name] = (listed, mentioned)
    return res

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--docs-ref', default='master'); ap.add_argument('--spec-ref', default='main')
    ap.add_argument('--spec'); ap.add_argument('--docs'); ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    spec = json.load(open(a.spec)) if a.spec else json.loads(get(SPEC.format(a.spec_ref)))
    doc = open(a.docs).read() if a.docs else get(DOCS.format(a.docs_ref))
    sm, dm = spec_methods(spec), doc_methods(doc)
    report = {'spec_version': spec.get('info', {}).get('version'),
              'only_in_docs': sorted(set(dm) - set(sm)), 'only_in_spec': sorted(set(sm) - set(dm)),
              'methods': {}}
    for name in sorted(set(sm) & set(dm)):
        ins, outs = sm[name]; listed, mentioned = dm[name]
        spec_all = ins | outs
        r = {'spec_not_in_docs': sorted((spec_all - mentioned) - IGNORE),
             'docs_not_in_spec': sorted((listed - spec_all) - IGNORE)}
        if r['spec_not_in_docs'] or r['docs_not_in_spec']:
            report['methods'][name] = r
    if a.json:
        json.dump(report, sys.stdout, indent=2); print(); return
    print(f"# monero-docs {a.docs_ref} vs monero-open-rpc daemon spec {report['spec_version']}")
    print("Documented JSON-RPC methods missing from spec:", ', '.join(report['only_in_docs']) or 'none')
    print("Spec methods missing from docs:", ', '.join(report['only_in_spec']) or 'none')
    for name, r in report['methods'].items():
        print(name)
        if r['spec_not_in_docs']: print('    in spec, not in docs:', ', '.join(r['spec_not_in_docs']))
        if r['docs_not_in_spec']: print('    in docs, not in spec:', ', '.join(r['docs_not_in_spec']))

if __name__ == '__main__':
    main()
