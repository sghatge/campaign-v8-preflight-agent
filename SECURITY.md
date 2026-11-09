# Security & data policy

## What this repo is
A read-only pre-flight checker that runs on **synthetic** campaign metadata. It has no network code, no Adobe Campaign connection, and no ability to send, schedule, or modify deliveries. CI enforces this: `tests/test_safety_guards.py` fails the build if engine code imports any network, mail, or process-spawning module.

## Never commit
- Real customer data, recipient lists, or exports from any Adobe Campaign instance
- Instance URLs, operator logins, API keys, tokens, or `.env` files
- Client or employer identifiers, internal hostnames, or screenshots of real consoles

CI runs a leak guard (emails, phone numbers, common token formats, card numbers, private keys) on every push. It is a safety net, not a substitute for review.

## If something sensitive is committed
1. Make the repo private immediately.
2. Rotate any exposed credential. Removing it from history is not enough.
3. Purge it from history (`git filter-repo` or BFG), then force-push.
4. Re-run the leak guard before making the repo public again.

## Reporting
Open a GitHub issue *without* sensitive details and ask for a private contact channel.
