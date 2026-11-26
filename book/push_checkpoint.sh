#!/usr/bin/env bash
# Publish a single checkpoint from the exact source revision that was tested.
set -euo pipefail

branch=${1:?target branch required}
attempts=${2:?retry limit required}
target="refs/heads/$branch"
git check-ref-format "$target"
checkpoint=$(git rev-parse --verify HEAD)
base=$(git rev-parse --verify HEAD^)

for ((attempt = 1; attempt <= attempts; attempt++)); do
  if git fetch origin "$target"; then
    upstream=$(git rev-parse --verify FETCH_HEAD)
    if [[ "$upstream" == "$checkpoint" ]]; then
      exit 0
    fi
    if [[ "$upstream" != "$base" ]]; then
      echo "CHECKPOINT_CONFLICT: $target moved from $base to $upstream; rerun against the current branch" >&2
      exit 1
    fi
    if git push origin "HEAD:$target"; then
      exit 0
    fi
  fi
  if [[ "$attempt" -lt "$attempts" ]]; then
    sleep "$((attempt * 3))"
  fi
done
echo "CHECKPOINT_PUSH_FAILED: could not publish $checkpoint to $target" >&2
exit 1
