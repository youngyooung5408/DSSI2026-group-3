---
name: prepare-work-record
description: Check submission readiness, inspect intended repository changes, and prepare a dated work-trace Markdown record when a student asks to commit, push, submit to GitHub, or obtain submission commands. Diagnose rejected submissions while leaving Git mutations to the student.
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

## Submission readiness

Before handing off commit or push commands:

- Establish the current branch, target branch, upstream, staged scope, and any
  active merge/rebase or unresolved paths. When an operation is paused, complete
  its recovery workflow before proposing another pull, branch switch, or push.
- For a push, compare the intended local tip with the remote target. Label cached
  tracking refs as cached; use an available read-only remote lookup when needed.
  A remote-tip lookup alone does not provide missing commit objects. If upstream
  commits need integrating, provide student-run synchronization and conflict
  checkpoints before the push. This need not prevent a local commit. Never fetch
  or rewrite history yourself merely to perform the check.
- Scan the explicit intended files, including untracked additions and downloaded
  HTML/JSON configuration, for credential patterns before recommending a commit.
  Inspect the repository scanner's actual scope and coverage. Its default tracked
  working-tree scan may omit untracked files; an empty staged scan is not evidence
  that a nonempty submission was checked. Report unreadable or unsupported content
  and known detector limits. Zero matches does not guarantee GitHub acceptance.
- Inspect whether the expected hook is executable and active in this clone,
  including `core.hooksPath` and the effective hook directory. A checked-in hook
  file alone does not activate it. Do not install hooks or change Git configuration
  silently. If inactive, include a manual staged scan in the student's handoff.
- Require a scan of the actual staged snapshot after the student stages changes
  and before committing. For a push of existing commits, scan the unpublished
  commits being sent, not just the working tree or latest snapshot. A later
  deletion does not remove a token from an earlier unpublished commit.
- Make handoff commands stop on a failed scan, conflict, or rejected operation.
  Use separate checkpoints or success-conditional commands rather than a block
  that keeps committing/pushing after an earlier failure. Recheck state after a
  rebase or amend because commit IDs and the pending range can change.

For hook/scanner scope details, synchronization checkpoints, or any rejected Git
operation, read [submission checks and recovery](references/git-submission-recovery.md).
Keep checks proportional to the actual submission; do not require unrelated
research reruns, install a new service, or change repository rules as a preflight.

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
  hash. Do not amend existing history just to include the record. This does not
  preclude student-run repair of an unpublished commit rejected for a credential;
  use the linked recovery guidance and verify its publication status first.
- When the student later reports completion, inspect available evidence
  read-only and update the same record's status if requested. Apply `AGENTS.md`
  push-verification rules; a clean worktree or cached remote-tracking ref alone
  does not establish remote publication. Any record update needs a subsequent
  student commit; do not create another record solely to document that update.
