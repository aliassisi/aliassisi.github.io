#!/usr/bin/env python3
"""Add a content version to links to our own CSS and JS files.

Usage:
    python3 -I .github/scripts/version_assets.py SITE_DIR

The deploy and preview workflows run it on their copy of the site. It does not
need to run on the repo, and its output is not committed.

Browsers (Safari on iPhone above all) keep CSS and JS for hours. Without a
version in the URL a phone can show a new page with old styles. This script
turns every href/src that points to assets/alia/<file>.css or .js into
assets/alia/<file>.css?v=<first 8 hex of the file's SHA-1>, so the URL changes
whenever the file changes.

A link that already has a query string is left alone.
Running it twice gives the same result.
"""
import hashlib
import os
import re
import sys

LINK = re.compile(
    r"""(?P<attr>(?:href|src)=)(?P<q>['"])(?P<url>[^'"?#]*assets/alia/(?P<path>[^'"?#]+\.(?:css|js)))(?P=q)"""
)


def main(site):
    hashes = {}

    def version(path):
        if path not in hashes:
            full = os.path.join(site, 'assets', 'alia', *path.split('/'))
            try:
                with open(full, 'rb') as f:
                    hashes[path] = hashlib.sha1(f.read()).hexdigest()[:8]
            except OSError:
                hashes[path] = None
        return hashes[path]

    pages = changed = links = 0
    for d, dirs, names in os.walk(site):
        dirs[:] = [x for x in dirs if x not in {'.git', '.github', '.claude', 'pagefind'}]
        for n in names:
            if not n.endswith('.html'):
                continue
            p = os.path.join(d, n)
            try:
                with open(p, encoding='utf-8', newline='') as f:
                    s = f.read()
            except UnicodeDecodeError:
                continue  # revslider ships binary cursors named *.cur.html
            pages += 1
            count = 0

            def sub(m):
                nonlocal count
                v = version(m.group('path'))
                if not v:
                    return m.group(0)
                count += 1
                return f"{m.group('attr')}{m.group('q')}{m.group('url')}?v={v}{m.group('q')}"

            t = LINK.sub(sub, s)
            if t != s:
                with open(p, 'w', encoding='utf-8', newline='') as f:
                    f.write(t)
                changed += 1
                links += count
    missing = sorted(k for k, v in hashes.items() if v is None)
    print(f'{pages} pages, {changed} changed, {links} links versioned')
    if missing:
        print('not found, left as is:', ', '.join(missing))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
