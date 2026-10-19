## Pi host

This lead runs in the main Pi 1.0 conversation. Start `pi` in the project folder
and invoke `/{{LEAD_AGENT}} <task>` to load these instructions as a prompt template.
Use the available `read`, `bash`, `edit` and `write` tools to do the work yourself.
Tool availability follows the operator's Pi configuration; a template grants no
permissions and creates no child session.

Invoke `/skill:{{CHECKPOINT_NAME}}` before handover; append `fresh` when requesting
a successor. Ask the operator to start `pi` in the same project and invoke
`/{{LEAD_AGENT}} Read LEAD.md and resume the recorded next action.` Re-load the
lead template in a new conversation. Run `/reload` after installing or updating
these resources in an already-open Pi session.
