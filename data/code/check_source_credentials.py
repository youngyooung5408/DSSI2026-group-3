#!/usr/bin/env python3
"""Read-only credential-pattern check. Prints locations/types, never matched values.

Default scans tracked working-tree bytes. Use --staged immediately before commit,
or --commit REV to inspect a historical tree without changing Git state.
A clean result covers these patterns only; it does not validate/revoke credentials.
"""
import argparse
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
PATTERNS = {
    'Tencent WeChat App ID': rb'(?<![A-Za-z0-9])wx[0-9a-f]{16}(?![A-Za-z0-9])',
    'Google API key': rb'AIza[0-9A-Za-z_-]{35}',
    'AWS access key ID': rb'(?:AKIA|ASIA)[A-Z0-9]{16}',
    'GitHub token': rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})',
    'OpenAI-style key': rb'sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{40,}',
    'Private-key header': rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    'Slack token': rb'xox[baprs]-[A-Za-z0-9-]{20,}',
    'Stripe secret': rb'sk_(?:live|test)_[A-Za-z0-9]{20,}',
}

def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], stderr=subprocess.PIPE)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--staged', action='store_true')
    mode.add_argument('--commit', metavar='REV')
    args = parser.parse_args()
    if args.commit:
        rev = git('rev-parse', '--verify', args.commit + '^{commit}').decode().strip()
        paths = git('ls-tree', '-r', '--name-only', '-z', rev).split(b'\0')
        load = lambda p: git('show', rev + ':' + p)
        label = 'commit ' + rev[:12]
    elif args.staged:
        paths = git('diff', '--cached', '--name-only', '--diff-filter=ACMR', '-z').split(b'\0')
        load = lambda p: git('show', ':' + p)
        label = 'staged additions/modifications'
    else:
        paths = git('ls-files', '-z').split(b'\0')
        load = lambda p: (ROOT / p).read_bytes() if (ROOT / p).is_file() else b''
        label = 'tracked working-tree files'
    count = total = 0
    for raw_path in paths:
        if not raw_path:
            continue
        path = raw_path.decode('utf-8', 'surrogateescape')
        data = load(path)
        count += 1
        for kind, pattern in PATTERNS.items():
            for match in re.finditer(pattern, data):
                line = data.count(b'\n', 0, match.start()) + 1
                print(f'{path}:{line}: {kind} [VALUE REDACTED]')
                total += 1
    print(f'Checked {count} {label}; {total} credential-pattern matches. No values displayed.')
    return 1 if total else 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, subprocess.CalledProcessError):
        print('Credential check could not read the requested files; stopping without displaying data.', file=sys.stderr)
        sys.exit(2)
