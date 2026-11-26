# Hakim continuation exchange

Hakim, Dot, ChatGPT Work, and automations can use this UTF-8 JSON format to exchange a concise checkpoint through a locally accessible file. The CLI uses Python's standard library to validate records and to store approved handoffs in a local SQLite inbox. [example.json](example.json)

```sh
python -m interop check interop/example.json --for dot
python -m interop check received.json --for chatgpt-work --previous previous.json
```

## Record format

Supply each field exactly once, with no additional fields. The total UTF-8 size is limited to 16,384 bytes. Intent and outcome summaries are single lines of at most 500 Unicode characters.

| Field | Value |
| --- | --- |
| `schema` | Literal `hakim.continuation/v1`. |
| `producer`, `recipient` | Two distinct labels from `hakim`, `dot`, `chatgpt-work`, `automation`. |
| `goal_id` | Stable identifier of 1–96 ASCII characters. Starts with a letter or digit. Subsequent characters may also include `.`, `_`, or `-`. |
| `revision` | Integer from 1 through 9,007,199,254,740,991. Increases per `(goal_id, producer, recipient)` stream. |
| `updated_at` | UTC timestamp in `YYYY-MM-DDTHH:MM:SSZ` form, with optional fractional seconds of up to six digits. |
| `status` | `active`, `waiting`, `blocked`, `complete`, or `cancelled`. |
| `goal_label`, `stage` | Nonempty intent and phase summaries. |
| `last_verified` | Concise account of the latest confirmed result or an empty string before verification. |
| `next_step` | The next step to consider. Use an empty string for `complete` or `cancelled`. |
| `blocker` | Verified impediment summary. Required for `blocked`. Use an empty string when there is none. |

The continuation record retains the goal, phase, next step, and confirmed outcome called for in the repository's historical continuity contracts. For a legacy `app/continuity.py` snapshot, `mission_id` maps to `goal_id`, `phase` to `stage`, and `next_action` to `next_step`. The sender summarizes verified evidence in `last_verified` and maps status to the values above. [Historical continuity state](https://github.com/smileeyes1/delegated-ai-agent/blob/39814bb5dd2e56fcd5000c3de3fae4ec857f0a2e/app/continuity.py)

## Checking a checkpoint

1. Obtain the file through an already authorized transfer. Use operational summaries and omit credentials, raw device data, and private payloads.
2. Check for the intended recipient and supply that stream's last accepted file using `--previous` when one exists. A valid record reports `new`, `advanced`, or `duplicate` as JSON. Validation fails on a stale revision, conflicting content at the same revision, or a previous record from a different stream. Consumers can retain the accepted record to recognize duplicates on the next receipt.
3. Treat `producer` as a routing label. The receiver verifies identity through the chosen transport, verifies material claims against trusted evidence, and applies its own authorization before acting on a next step.

This format has a local CLI. A service deployment needs an adapter using that service's authorized access and its own storage for the last accepted record.

## Receiving an approved file

The local adapter accepts an exact file on an explicitly selected producer-to-recipient route. Supply the SHA-256 digest obtained through a route you trust independently of the received file. For a local sender and receiver, the sender can publish the digest of its reviewed export through a trusted channel before sending the file. An approval concerns inbox receipt of the specified bytes. Authorization for any action mentioned in the checkpoint comes from the recipient's execution controls.

```sh
python -m interop receive incoming.json --db inbox.sqlite3 \
  --from hakim --for dot --sha256 "$APPROVED_CHECKPOINT_DIGEST"
python -m interop latest book-factory-e2e --db inbox.sqlite3 \
  --from hakim --for dot > resumed.json
```

`receive` records an accepted revision and returns its digest, receipt time, and disposition. Each stream advances independently. An exact retry returns the original receipt as `duplicate`. A stale revision or different bytes at an accepted revision fail. Competing processes compare and store revisions in one SQLite transaction. Use regular files for inputs and an inbox in a private directory on a local filesystem. Each accepted revision retains its exact bytes. `latest` verifies stored identity and digest and emits the latest record as received.

For integrations in the same Python process, `interop.receiver.receive_file` and `interop.receiver.latest_record` supply the same checks without spawning the CLI. Python callers supply the already approved route and digest from their own trusted context.
