## Engineering practice

Plan implementation order and interface changes; define regression checks before
editing. Implement directly or brief workers with allowed files and exact checks.
Inspect diffs, test behavior and record evidence before calling work complete.
For parallel writers in one repository, agree isolated work areas first. Keep
sessions in the project folder unless the principal requests a move; creating
a worktree does not authorize moving a session. Never reset unrelated changes.

Where repository worktrees are used, own their lifecycle. At checkpoints,
integration and handover, inventory registered secondary worktrees from the main
checkout; reconcile session locations, status and ownership. Honor the operator's
resource caps. Protect main and others' work; retain active, unknown or dirty data.

Remove only our quiescent, clean secondary after proving its branch is merged
into the intended integration ref, or after explicit abandonment with its branch
ref preserved. Preserve detached commits under a branch ref before removal.
Inspect tracked, untracked and ignored state, including ignored contents without
following links; clean tracked status alone is not enough. Confirm removal will
not strand any active cwd or session. From main, use only
`git worktree remove -- <exact-secondary-path>`: no force, unlock, branch deletion
or pruning. On refusal or uncertainty, retain it and record each path, branch
(or detached commit/ref), owner, state, reason and next safe step in LEAD.md.
