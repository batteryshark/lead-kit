Never pass a `directory` other than your own to `a2a_create`: that makes a top-level session,
which goal mode doesn't wait for. When parallel workers would touch the same repository, create a
git worktree inside the project (for example `wt/<name>`) and tell the worker to work there.
