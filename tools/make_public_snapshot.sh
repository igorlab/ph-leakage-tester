#!/bin/sh
# Build a clean copy of the repository for publication: no git history, no working notes
# (see .gitattributes), README_PUBLIC.md as README.md.
# Usage: tools/make_public_snapshot.sh /path/to/empty/dir
set -e
dest="$1"
[ -n "$dest" ] || { echo "usage: $0 <empty dir>" >&2; exit 1; }
mkdir -p "$dest"
[ -z "$(ls -A "$dest")" ] || { echo "$dest is not empty" >&2; exit 1; }
git archive HEAD | tar -x -C "$dest"
mv "$dest/README_PUBLIC.md" "$dest/README.md"
echo "Snapshot written to $dest. Review it, then 'git init' there for the first public commit."
