---
description: Leads project implementation, verification and handovers.
mode: primary
permissions:
  - action: shell
    resource: "rm *"
    effect: ask
  - action: shell
    resource: "git push*"
    effect: ask
  - action: shell
    resource: "git reset*"
    effect: ask
  - action: shell
    resource: "git clean*"
    effect: ask
---
{{MARKER}}

{{PROMPT}}
