# Lead checkpoint

This lead's checkpoint resource is `{{CHECKPOINT_NAME}}`. Use that same resource
for automatic checkpoints and before handover; do not substitute a default checkpoint.

Sweep the conversation into LEAD.md and lead/: goal, decisions, waiting items,
promises, failed approaches, stop conditions, evidence, workers and side effects.
Keep Status at most ten lines; archive old decisions and attempts, never principal
decisions. Reconcile worker state and report unknowns honestly. Check the header's
configured reports-to mode and live pointer, if any. Read the log as a fresh lead:
can it resume without this conversation? Fix omissions before reporting completion.

For `fresh`, first checkpoint, then create a new session in the same outcome folder
using agent `{{LEAD_AGENT}}`, title `[lead] <Project>`, the exact logged goal and goal
mode where supported. Update the log header with its id. Notify the configured
owner through the configured mode, and tell running workers the new id. Forward
late arrivals. The continuing lead uses `{{CHECKPOINT_NAME}}` too. Never require a
chief or its memory for this workflow.
