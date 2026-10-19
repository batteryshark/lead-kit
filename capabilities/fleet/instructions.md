## Capability: Fleet

Fleet is external, optional and macOS-specific. If the operator has configured
Fleet, read that installation's README and use `fleet add` or `fleet adopt`
with port, health probe and group for an approved background service. Check its
registry (`~/.config/fleet/services.json`) first; do not duplicate adoption.
Registration is necessary, not permission to install. Without Fleet, ask the
operator for the approved service-management process; do not invent one.
