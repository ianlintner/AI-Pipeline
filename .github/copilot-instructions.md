## Caretaker

This repo uses the [caretaker](https://github.com/ianlintner/caretaker) autonomous
maintenance system. The orchestrator runs weekly via GitHub Actions and assigns tasks to
`@copilot` via structured issue and PR comments.

Agent instruction files live in `.github/agents/`:
- `maintainer-pr.md` — how to respond to PR fix requests
- `maintainer-issue.md` — how to execute assigned issues
- `maintainer-upgrade.md` — how to apply caretaker upgrades

Always check these files when you receive a caretaker assignment.
