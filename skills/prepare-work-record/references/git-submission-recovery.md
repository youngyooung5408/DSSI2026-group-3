# Git submission checks and recovery

Read the relevant sections when preparing a submission or diagnosing its failure.
All Git mutations remain student-operated under `AGENTS.md`. Reading status,
configuration, history, diffs and remote refs does not authorize installing hooks,
changing rules, staging, pulling, rebasing, amending or pushing for the student.

## Branch state and remote changes

1. Establish the repository, intended destination, local tip and upstream. Inspect
   status and unresolved paths, plus Git's merge/rebase state. A detached HEAD
   during a rebase is expected; do not solve it by switching branches.
2. Distinguish a cached upstream comparison from a fresh remote lookup. Read-only
   `git ls-remote` or an accessible GitHub API view can verify the target tip.
   Neither updates local history. If missing objects prevent an ancestry check,
   disclose it and let the student refresh/synchronize before claiming readiness.
3. If local history lacks upstream commits, a local commit can still be useful,
   but a normal push needs integration first. Protect dirty work and identify
   untracked path collisions before proposing a pull. Select merge or rebase from
   the existing workflow and publication status; do not universally prescribe a
   history rewrite or discard local/teammate changes.
4. If synchronization pauses, inspect the actual conflict. Authorized working-file
   edits may preserve both sides' substantive changes. Confirm conflict markers
   are gone and the affected content is coherent. Git still requires the student
   to stage the resolved paths and continue the existing operation. Check success
   before proposing a push; do not start another pull while it is paused.

## Credential scans and hook activation

- Read the scanner before choosing a mode. In this project,
  `data/code/check_source_credentials.py --staged` reads index blobs, its default
  mode reads tracked working files, and `--commit REV` reads one commit snapshot.
  None of those modes automatically means “all intended untracked files” or
  “every unpublished commit.” Use an explicit scoped read-only scan where needed.
- Scan the proposed nonempty file list during preparation, then the actual staged
  blobs before commit. Check that the reported paths/count cover the intended
  additions and modifications, including raw captures. A zero-file scan is a no-op
  when a nonempty submission is intended. Never expose matched values in logs.
- For existing unpublished commits, inspect a bounded, confirmed pending range
  and scan its commit versions/changed blobs. Scanning only HEAD misses a token
  added and removed in earlier commits. If the available scanner can inspect only
  snapshots, inspect each relevant commit or report the unverified range.
- Include HTML script configuration, JSON and serialized notebook outputs where
  applicable. Do not assume visible article text is the whole saved capture.
  Inspect pattern coverage, including Mapbox token forms when present. No finite
  pattern list exactly reproduces GitHub's detectors; name limitations rather than
  promising that zero local matches guarantees a successful push.
- Inspect `core.hooksPath`, the effective hook's existence/executable bit, and the
  interpreter/scanner it invokes. A file under `.githooks/` alone is inactive
  without matching configuration. Use a manual staged scan when inactive; provide
  student-run installation steps only within the requested setup scope.
- A pre-commit hook covers its configured checks at commit time. It does not by
  itself verify old unpublished commits or remote branch rules. Do not describe
  it as a complete push check. Keep later commit/push commands conditional on
  successful checks, and re-scan after content or history changes.

## Diagnose the reported rejection

Capture the relevant redacted stderr, especially server `remote:` lines, exit
status, rejected ref, rule identifier and file/commit locations. Keep local
warnings separate from the server reason. If the reason is missing, inspect
available read-only evidence and ask only for the missing error details. Do not
retry mutations simply to obtain a log.

| Observed reason | Response |
| --- | --- |
| Non-fast-forward / remote contains commits absent locally | Inspect ancestry and dirty state; have the student integrate upstream, resolve conflicts and recheck before pushing. |
| Rebase/merge in progress or unresolved paths | Recover the current operation first; preserve both parties' work and stage only the intended resolutions. |
| GH013 / push protection with credential locations | Follow the unpublished-credential repair below. |
| Required pull request, status checks or commit signatures | Identify the actual required workflow from the error or accessible rule details. Prepare that workflow; do not disable protection or assume direct push is allowed. |
| Authentication/permission failure | Confirm the repository and intended account/access without displaying credentials. Do not change identities or issue tokens silently. |

## Repair an unpublished credential-bearing commit

1. Identify the exact rejected commit(s) and paths. Do not print, test or use the
   credential. A webpage may embed a third-party token even when the research
   itself uses no API credentials. Follow the authorized
   [web-capture redaction procedure](../../raw-data-documentation/SKILL.md#web-captures-and-embedded-credentials)
   for source copies, provenance and fixed hashes.
2. Scan the corrected submission and determine whether the rejected commit is
   unpublished. Do not infer this solely from a cached ref. Use the actual
   rejection and available remote branch evidence, noting any uncertainty.
3. If the token appears in the latest unpublished commit, prepare the file repair
   and explain student-run `git commit --amend --no-edit` after explicit staging
   and a successful staged scan. A new cleanup commit alone leaves the token in
   the history being pushed. Earlier unpublished commits need a separately scoped
   student-run history repair; inspect the range before proposing commands.
4. Already published or shared history requires a different coordinated recovery.
   Do not automatically amend/rebase it or suggest force pushing. Do not revoke
   third-party credentials or claim removal revokes them. If an actual secret was
   exposed, identify the owner's rotation task without claiming it was done.
5. Do not use an unblock link, request bypass, weaken repository rules or force
   push as the routine fix. Recheck the rewritten range and the remote destination
   before the student's next push. Verify branch membership after success.

Reuse the current submission record for this recovery. Record the old rejected
SHA as historical, leave the rewritten SHA pending until observed, and keep local
commit, remote rejection and verified publication distinct.

## macOS AppleDouble files on external drives

When Git names `.git/objects/pack/._pack-*.idx` and reports a non-monotonic index,
inspect the named files' type/header read-only. AppleDouble metadata is distinct
from the real `pack-*.idx` and `pack-*.pack` objects. Do not assume every index
error has this cause, or blame these local messages for a separate server rule
rejection without evidence.

Repository `.gitignore` patterns do not clean metadata already inside `.git/`.
Do not silently delete objects or perform broad cleanup. If the student requests
repair, identify confirmed metadata files, back them up outside Git and prepare
narrow student-run quarantine instructions with checks that the real pack/index
pairs remain. Recheck the original Git command afterward. Actual object/index
corruption needs its own diagnosis rather than this metadata procedure.

## Official references

- [Git hooks and core.hooksPath](https://git-scm.com/docs/githooks)
- [Git push and fast-forward rules](https://git-scm.com/docs/git-push)
- [GitHub push-protection recovery](https://docs.github.com/en/code-security/how-tos/secure-your-secrets/work-with-leak-prevention/push-protection-on-the-command-line)

These references support the recovery mechanics; local course rules still decide
who executes Git mutations. Check current error/rule details before applying a
workflow rather than assuming a past repository configuration still applies.
