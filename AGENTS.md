When implementing new features or product requirements, fetch the latest
context from available MCP servers (e.g. Cupcake orders) before coding.

## Agent skills

### Issue tracker

Issues and specs live in GitHub Issues for `velkomic/cinemood`.
Read `docs/agents/issue-tracker.md` before tracker operations.

### Triage labels

Use the five default triage labels.
Read `docs/agents/triage-labels.md` before triaging issues.

### Domain docs

Single-context layout: root `GLOSSARY.md` and `docs/adr/`.
Read `docs/agents/domain.md` before exploring the codebase.

## Project planning and progress

Before planning or implementation, read `docs/PROJECT.md` for agreed scope and open decisions, and `docs/progress.md` for the active milestone and verified state. Keep these current when decisions or verification results change; distinguish proposals from accepted decisions and verified implementation.

For system design, read `docs/ARCHITECTURE.md` and relevant ADRs. For milestone sequencing, read `docs/ROADMAP.md`; its proposed slices become implementation work only after the specification and ticket breakdown are agreed.

For specification or ticket work, read `docs/SPEC.md` and `docs/plans/MVP.md`. Before starting a slice, confirm its review/publication status in `docs/progress.md`, read its full tracker issue when published, and check blockers. Update progress with verification evidence after completing a slice. Obtain explicit approval of the concrete resource/cost plan before provisioning paid AWS infrastructure.
