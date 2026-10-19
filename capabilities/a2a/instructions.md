## Capability: a2a

For an authorized peer task, use `a2a_list` to discover configured servers, then
`a2a_send` with an explicit server/session target and expectReply: true. Results
arrive automatically; `a2a_read` is for inspecting messages, not waiting. To create
a local worker where creation is permitted, use `a2a_create` (server: local,
nested by default), then `a2a_send`. Do not override its directory to simulate
nested work elsewhere. Creation must be explicitly authorized by the operator.
Answer a worker's incoming question in your reply; do not send an acknowledgement
that starts a loop. If these tools are absent, record the missing channel and
use native workers or do the work locally. This pack does not bind owner reporting.
