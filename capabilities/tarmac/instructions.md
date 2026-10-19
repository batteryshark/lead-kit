## Capability: Tarmac usage awareness

Use the independent Tarmac REST service only through an authorized HTTP tool
that can reach the operator-provided endpoint. Read its installed API guide and
confirm the base URL and any deployment-specific authentication with the operator.
No tool name, credential discovery or client runtime is supplied by this pack.
If the endpoint or HTTP access is missing, report usage as unknown and continue
within the stated resource budget; ask before work that needs additional capacity.

For the documented local API, make a bounded `GET /api/v1/snapshot` at that base
URL. Reads need no bearer token; Host must be `127.0.0.1` or `localhost`, and an
Origin, if sent, must also name a loopback host. Don't bypass that boundary or
search local auth files. Source mutations require a bearer token but are outside
this read-only workflow. Never trigger refresh, login, source changes or service
startup to obtain a reading. `/api/v1/status` and `/api/v1/meta` mark a reader
active; status can queue demand-source refreshes. Use the passive snapshot for
planning without those effects.

Require `schema_version: 2` and `passive: true`. Match `sources` by the operator's
account/provider mapping, then examine `fresh`, `status` and `latest`: its
`observed_at`, `fresh_until`, `definitive`, `reason` and individual `windows`.
Each window has an `id`, optional `bucket_id`, `unit`, `remaining_percent`,
`resets_at`, `stale` and reset precision. Despite the field name, interpret
`remaining_percent` using `unit`. Model-to-bucket applicability comes from the
operator; don't infer it from a provider name. Check every applicable window.
Treat missing, stale or unknown data as uncertainty about capacity and holds.
Absence from `holds` does not prove capacity. `window_burns` describes observed
consumption over its sample interval; it cannot predict a task's cost.

Use these observations to propose a resource allocation within the approved
budget, accounting for work already committed. Tarmac does not reserve capacity,
dispatch workers, buy credits or redeem resets. It requires no OpenChamber pack;
worker dispatch still uses the host's configured tools and authority.
