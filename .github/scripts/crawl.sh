#!/usr/bin/env bash
# Re-crawl the WordPress site and rebuild the static site in this repo.
#
# Usage: bash .github/scripts/crawl.sh [CRAWL_DIR]
#
# CRAWL_DIR holds the raw wget copy. It is outside the repo.
# It defaults to ../aliassisi-crawl.
# Set LIMIT=N to crawl only the first N URLs (a quick test).
# Set OUT=DIR to write the result there instead of into the repo.
#
# Direct edits to pages are lost by this script. Put them in postprocess.py.
set -euo pipefail

repo=$(cd "$(dirname "$0")/../.." && pwd)
crawl=${1:-$repo/../aliassisi-crawl}
out=${OUT:-}
urls=("$repo/.github/crawl/urls.crawl.txt" "$repo/.github/crawl/urls.extra.txt")
host=$(head -n1 "${urls[0]}" | sed -E 's#^https?://([^/]+)/.*#\1#')

mkdir -p "$crawl"
raw=$crawl/raw
list=$crawl/urls.all.txt
cat "${urls[@]}" | sort -u > "$list"
if [ -n "${LIMIT:-}" ]; then head -n "$LIMIT" "$list" > "$list.tmp" && mv "$list.tmp" "$list"; fi

wget_opts=(--force-directories --page-requisites --adjust-extension --convert-links
           --no-verbose --timeout=30 --tries=3 -e robots=off --directory-prefix="$raw")

# 1. The pages and everything they need.
echo "crawling $(wc -l < "$list") URLs from $host"
rm -rf "$raw"
wget "${wget_opts[@]}" --input-file="$list" 2>&1 | tail -n 3 || true

# 2. Short links (/?p=ID). Pages link to them. Save each one, and record
# where the server sends it.
ids=$(grep -rhoE '[?&]p=[0-9]+' "$raw/$host" --include='*.html' 2>/dev/null | grep -oE '[0-9]+' | sort -un || true)
pmap=$crawl/pmap.tsv
: > "$pmap"
for id in $ids; do
  head=$(curl -sI -m 30 "https://$host/?p=$id" || true)
  status=$(printf '%s' "$head" | head -n1 | awk '{print $2}')
  where=$(printf '%s' "$head" | tr -d '\r' | awk 'tolower($1)=="location:"{print $2}')
  printf '%s\t%s %s\n' "$id" "${status:-000}" "$where" >> "$pmap"
  wget "${wget_opts[@]}" "https://$host/?p=$id" >/dev/null 2>&1 || true
done
echo "short links: $(wc -l < "$pmap")"

# 3. Clean up. cleanup.py first, then postprocess.py.
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
python3 -I "$repo/.github/scripts/cleanup.py" "$raw/$host" "$pmap" "$tmp/site" "$host"
python3 -I "$repo/.github/scripts/postprocess.py" "$tmp/site"
python3 -I "$repo/.github/scripts/prune_plugins.py" "$tmp/site"

# 4. Put the result in place. Keep git, workflows, agent files.
dest=${out:-$repo}
mkdir -p "$dest"
rsync -a --delete --exclude .git --exclude .github --exclude .claude --exclude CLAUDE.md --exclude pagefind \
  "$tmp/site/" "$dest/"

# 5. Check links. The search index is rebuilt by the deploy workflow.
python3 -I "$repo/.github/scripts/check_links.py" "$dest"
echo "done. Review with: git -C $repo status"
