## Capability: Runway OpenChamber dispatch adapter

Use the operator's installed `runway` tool and routing/WORKFLOW.md contract.
Read that workflow before the first call. Before dispatch, read `usage` to check
allowances near reset or exhaustion; use `plan` to choose a route and `prepare`
to reserve admission. Dispatch the returned OpenChamber arguments without
inventing fields or changing global models, then `bind` the returned session.
Use `finish` only after checking idle state and recording completion or a
checkpoint. Prefer burnable allowance within the operator's policy. A `prefer`
override requires the user's request and expires at the observed reset.
Routing does not buy credits, redeem resets or send the worker prompt itself.
If the tool, workflow or reservation is unavailable, block routed dispatch and
ask for an approved route; continue local work that does not require admission.
