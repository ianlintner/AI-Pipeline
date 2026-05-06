## Caretaker

This repo uses the [caretaker](https://github.com/ianlintner/caretaker) autonomous
maintenance system. The orchestrator runs weekly via GitHub Actions and assigns tasks to
`@copilot` via structured issue and PR comments.

Agent instruction files live in `.github/agents/`:
- `maintainer-pr.md` — how to respond to PR fix requests
- `maintainer-issue.md` — how to execute assigned issues
- `maintainer-upgrade.md` — how to apply caretaker upgrades

Always check these files when you receive a caretaker assignment.

<!-- Added by caretaker -->

## Caretaker System

This repository uses the caretaker automated management system.

### How it works

- An orchestrator runs weekly via GitHub Actions
- It creates issues and assigns them to @copilot for execution
- When @copilot opens PRs, the orchestrator monitors them through CI, review, and merge
- The orchestrator communicates with @copilot via structured issue/PR comments

### When assigned an issue by caretaker

- Read the full issue body carefully — it contains structured instructions
- Follow the instructions exactly as written
- If unclear, comment on the issue asking for clarification
- Always ensure CI passes before considering work complete
- Reference the agent file for your role: `.github/agents/maintainer-pr.md` or `maintainer-issue.md`

### Conventions

- Branch naming: `maintainer/{type}-{description}`
- Commit messages: `chore(maintainer): {description}`
- Always run existing tests before pushing
- Do not modify `.github/maintainer/` files unless explicitly instructed
