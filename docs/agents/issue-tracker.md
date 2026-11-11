# Issue tracker: GitHub

Issues and specs live in GitHub Issues for `velkomic/cinemood`.
Use the `gh` CLI from this repository.

If `gh` is unavailable, use the connected GitHub tools for the same repository. Verify repository identity before writing. When those tools do not expose native sub-issue/dependency mutations, use the relationship convention below and record that limitation in progress.

## Operations

- Verify the target: `gh repo view --json nameWithOwner`.
- Create: `gh issue create --title "..." --body-file <file>`.
- Read: `gh issue view <number> --json number,title,body,labels,comments`.
- List: `gh issue list --state open --json number,title,body,labels`.
- Comment: `gh issue comment <number> --body-file <file>`.
- Label: `gh issue edit <number> --add-label "..."`.
- Remove a label: `gh issue edit <number> --remove-label "..."`.
- Close: post an explanation, then `gh issue close <number>`.

Use native GitHub sub-issues and issue dependencies when supported.
Otherwise, put `Part of #<parent>` and `Blocked by: #<number>` at
the top of the issue body. An issue is unblocked when all blockers
are closed.

File issues only in the user's repository. Verify the target before
the first issue creation of a session.

## Pull requests as a triage surface

**PRs as a request surface: no.**

## Skill terminology

“Publish to the issue tracker” means create a GitHub issue.
“Fetch the relevant ticket” means read the GitHub issue.
