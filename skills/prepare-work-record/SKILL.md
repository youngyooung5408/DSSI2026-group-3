---
name: prepare-work-record
description: Inspect intended repository changes and prepare a dated work-trace Markdown record when a student asks to commit, push, submit changes to GitHub, or obtain shell commands for submission. Leave staging, commits, and pushes to the student.
---

# Prepare a Work Record Before Submission

Generate the record during the conversation before handing off student-run Git
commands. This skill is not a hook or a background GitHub monitor. Preserve the
student-operated Git rules in `AGENTS.md`; do not execute Git mutations.

## Inspect the intended changes

- Confirm the repository root and configured remote read-only, following
  `AGENTS.md`. Do not display credentials embedded in remote URLs.
- Inspect `git status --short`, `git diff`, `git diff --cached`, and untracked
  file paths. Read relevant new files separately: ordinary diffs omit them.
  Compare working files with HEAD while distinguishing staged and unstaged
  changes. A push-only request may instead concern existing unpushed commits;
  inspect their actual diffs and describe that commit range explicitly.
- Use the student's requested scope and conversation context. Do not include
  unrelated dirty files merely because they exist. If the intended submission
  cannot be determined, ask which changes belong while continuing read-only
  inspection. Do not guess the baseline for already committed work when local
  history and context cannot establish it.
- For notebooks, focus on source and relevant saved outputs rather than dumping
  output blobs. For binary or large files, record observable metadata and limits
  of inspection. Never copy credentials or sensitive raw content into the record.
- Describe substantive differences, not just commit messages or file counts.
  Distinguish observed changes from reported intent. A saved output is not proof
  that this session executed it; report only checks actually performed, and label
  previous or student-reported results with their source.

## Write the record

Create `attachments/meetings/work record/YYYY-MM-DD-HHMMSS.md`, using the actual
record creation time in `Asia/Taipei`. This is not a claimed commit or push time.
If the name exists, append `-02`, `-03`, etc.; never overwrite an existing record.
Use Traditional Chinese with Taiwan terminology unless explicitly requested
otherwise. Use relative Markdown links to relevant project files.

Use a concise title and these sections, scaled to the size of the change:

1. **紀錄資訊**: creation time and timezone, branch, comparison baseline/range,
   intended submission scope, and status. Identify the person only from confirmed
   session identity; do not assign the repository owner's name or student ID to
   an unidentified teammate. Distinguish commit authors from confirmed contributors.
2. **本次變更**: explain the before/after behavior or content, purpose supported
   by evidence, and relevant file links. Note additions, deletions, or renames
   when material. Do not equate a commit with correctness or completed research.
3. **驗證與限制**: checks actually performed and their outcomes; explicitly mark
   unexecuted checks, unreadable artifacts, or missing evidence. Do not launch
   expensive analysis solely to make the record appear verified.
4. **尚待處理**: remaining work and known limitations; say none identified if
   appropriate, without inventing tasks.
5. **提交範圍與狀態**: intended files, the new record itself, and relevant dirty
   files excluded from this submission. Start uncommitted work at `待提交`;
   for existing commits use the precise status rules in `AGENTS.md`. Never invent
   a future SHA or claim a push succeeded.

If there are no substantive changes or new unrecorded commits to describe,
explain that finding instead of generating an empty or duplicate record. Reuse
an existing pending record for the same intended submission, updating it if
needed; create a new timestamped record for a genuinely new submission scope.

## Hand off to the student

- Review the resulting diff and links, and verify that the record agrees with
  the inspected changes. Keep unrelated files and management records untouched.
- Provide shell commands for the student to inspect, stage explicit intended
  paths (including this record), commit with a descriptive message, and push to
  the confirmed destination. Quote paths safely, including spaces. Avoid
  blanket staging, force pushes, or branch/remote changes. If the destination
  is ambiguous, provide review commands and resolve it before giving a push
  command that assumes a target. Never run the mutation commands yourself.
- For an already committed change, explain that the record requires a separate
  student commit; reference the earlier artifact commit, not the record's future
  hash. Do not amend existing history just to include the record.
- When the student later reports completion, inspect available evidence
  read-only and update the same record's status if requested. Apply `AGENTS.md`
  push-verification rules; a clean worktree or cached remote-tracking ref alone
  does not establish remote publication. Any record update needs a subsequent
  student commit; do not create another record solely to document that update.
