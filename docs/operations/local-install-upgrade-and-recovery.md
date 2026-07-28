# Local Install, Upgrade, and Recovery

## Scope and Safety Boundary

This runbook covers the local Founder-only Standard and disposable Demo
workspaces. It does not provide cloud deployment, automatic backup, scheduled
retention, encryption/key management, disaster recovery, or a destructive
Standard reset command.

The current product migration chain is exactly:

```text
0001_product_baseline
  -> 0002_artifact_index
  -> 0003_paper_jobs
  -> 0004_paper_job_recovery_audit
  -> 0005_paper_job_result_references
  -> 0006_portfolio_reviews
  -> 0007_paper_account_ledger
  -> 0008_market_time_foundation
```

`0008_market_time_foundation` is the single current head. Supported Founder
upgrades move forward to that head. Alembic downgrade is developer/test
behavior, not a supported Founder recovery path.

Standard and Demo remain isolated:

| Mode | Compose project | Named volume | Workspace root |
|---|---|---|---|
| Standard | `el-psy-quant-mvp` | `mvp-data` | `/data` |
| Demo | `el-psy-quant-demo` | `demo-data` | `/data/workspace` |

Never run a volume-removing command against the Standard project. Demo reset is
allowed only through the complete Demo overlay command shown below.

## Locked Installation Inputs

Python development and CI installation uses the committed `uv.lock`:

```powershell
uv sync --locked
uv lock --check
```

`requirements-build.txt` and `requirements-runtime.txt` are the exact
pip-compatible exports used by the backend image. The first contains only the
PEP 517 backend and its build dependencies; the second contains only product
runtime dependencies. Regenerate and check both with the installed reviewed
`uv` version:

```powershell
uv export --locked --only-group build --no-emit-project --no-hashes --no-annotate --no-header --output-file requirements-build.txt
uv export --locked --no-dev --no-emit-project --no-hashes --no-annotate --no-header --output-file requirements-runtime.txt
uv run python scripts/check_build_requirements.py
uv run python scripts/check_runtime_requirements.py
```

The builder stage installs only the exact build export and creates the local
wheel with dependency resolution and build isolation disabled. The final stage
installs the exact runtime export and that wheel with dependency resolution
disabled; build and test dependencies are not copied into the final image. The
wheel owns the complete single Alembic resource tree, and `alembic.ini` resolves
that installed-package authority without `/app/src` or a repository checkout.
The Web image continues to use `package-lock.json` through `npm ci`.

These locks do not make a cold image build offline. Uncached base images,
package artifacts, and floating upstream image tags still require an available
source and can change or become unavailable outside the reviewed repository.
No proxy configuration belongs in the project.

## Fresh Standard Startup

Create the local uncommitted credential file:

```powershell
Copy-Item .env.example .env
```

Replace the password placeholder, then let the Founder-owned Docker runtime
build and start:

```powershell
docker compose up --build --detach
docker compose ps
```

Before Uvicorn starts, the backend:

```text
creates only absent /data/research, /data/evidence, and /data/paper directories
  -> if product.sqlite3 exists, reads exactly one approved 0001-0007 revision
     without writes; a missing file follows the fresh-install path
  -> runs the forward Alembic upgrade
  -> verifies /data read-only in Standard mode
  -> starts Uvicorn
```

An existing file with a missing table, zero or multiple revision rows,
malformed SQLite, or an unknown/newer revision is refused before Alembic and
remains untouched.

An empty research, evidence, Paper Job, or paper-output collection is valid. The
startup path never invokes the Demo installer and never resets, truncates,
downgrades, replaces, or seeds Standard state.

Run an explicit post-start read-only verification and the bilingual,
non-mutating same-origin smoke:

```powershell
docker compose exec backend el-psy-quant verify-local-workspace --mode standard --workspace-root /data
docker compose exec web node /app/verify-mvp.mjs
```

The verifier prints only bounded mode/revision identity. The smoke checks
authenticated FastAPI health, English and Simplified Chinese document identity
and copy, locale switch/restoration, top-level and representative detail
routes, valid empty reads, stable raw values, request IDs on authenticated
backend responses and backend failures, and sanitized errors. The Web
proxy-owned unauthenticated Basic challenge is checked without claiming a
backend request ID. Verification sends no Paper Job, portfolio-review,
lifecycle, or Paper Account mutation command.

## Cold Backup Before a Standard Upgrade

Backup is an explicit Founder action. Startup never performs it.

1. While the current Standard service is healthy, record the source application
   commit and verify the source schema:

   ```powershell
   git rev-parse HEAD
   docker compose exec backend el-psy-quant verify-local-workspace --mode standard --workspace-root /data
   ```

2. Record those two outputs beside the backup as operator-owned text metadata.
3. Stop the complete Standard stack without deleting its volume:

   ```powershell
   docker compose stop
   ```

4. Copy the complete stopped `/data` tree as one versioned backup set:

   ```powershell
   New-Item -ItemType Directory -Force C:\path\to\el-psy-quant-backups\standard-YYYYMMDD-HHMMSS
   docker compose cp backend:/data/. C:\path\to\el-psy-quant-backups\standard-YYYYMMDD-HHMMSS\
   ```

The backup set must keep `product.sqlite3`, `research/`, `evidence/`, and
`paper/` together. Copying only SQLite is not a complete workspace backup.
Copying a live SQLite file is not claimed to be transactionally consistent.
The Founder is responsible for permissions and security of the external backup
location.

## Upgrade an Existing Standard Volume

After the cold backup is complete:

```powershell
git switch <reviewed-commit-or-branch>
docker compose up --build --detach
docker compose ps
```

Startup forwards the existing database to the one current head, verifies the
exact tables and columns read-only, and only then serves. Repeating startup at
head is a no-op for existing rows and authoritative artifact files.

Run the post-upgrade checks:

```powershell
docker compose exec backend el-psy-quant verify-local-workspace --mode standard --workspace-root /data
docker compose exec web node /app/verify-mvp.mjs
```

If migration or verification fails, Uvicorn does not start. Do not delete the
volume, edit `alembic_version`, downgrade, reset, reinstall over the data, or
copy only selected files as a repair. Preserve the failed volume and logs for
diagnosis, retain the cold backup, and review the code/configuration mismatch.

## Sprint 177 Preserved-Volume Recovery

Founder Standard startup before Sprint 177 failed because the runtime-only image
installed the project wheel but `alembic.ini` still pointed at repository source
under `/app/src`. The stopped Standard database was healthy at exact revision
`0005_paper_job_result_references`, the expected 0005 tables and data were
present, the complete cold backup was retained, and the same database upgraded
successfully through repository-source migrations. The defect was migration
resource location, not database corruption, schema drift, partial 0006 state,
permissions, or volume identity.

After the Sprint 177 fix is reviewed and merged:

1. Keep the existing complete cold backup. Do not replace, remove, reset, or
   recreate the Standard volume.
2. Do not hand-edit or stamp `alembic_version`, downgrade the database, or copy
   selected files over the preserved workspace.
3. Rebuild the backend image from the reviewed commit and start it against the
   same preserved Standard volume.
4. Confirm startup performs the supported
   `0005_paper_job_result_references -> 0006_portfolio_reviews` upgrade and only
   serves after read-only workspace verification succeeds.
5. Run the read-only Standard verification and bilingual MVP smoke shown above.
6. Continue Demo v3 reset/install, exact Paper Account and portfolio-review
   replay, persistence, return to Standard, volume-isolation, and bilingual
   browser acceptance.

The Founder owns every Docker and browser step in this recovery. Sprint 177
repository checks do not claim runtime acceptance, and Sprint 178 closeout
remains blocked until the preserved-volume recovery and complete Standard/Demo
acceptance succeed.

## Fresh Demo, Exact Replay, Reset, and Return

Stop Standard without deleting its volume, then start the complete Demo overlay:

```powershell
docker compose down
docker compose -f compose.yaml -f compose.demo.yaml up --build --detach
docker compose -f compose.yaml -f compose.demo.yaml ps
```

Demo startup validates the complete source, installs atomically or recognizes
the exact marker/digest replay, forward-upgrades the Demo database, verifies the
descriptor-owned journey read-only, and only then serves.

```powershell
docker compose -f compose.yaml -f compose.demo.yaml exec backend el-psy-quant verify-local-workspace --mode demo --workspace-root /data/workspace
docker compose -f compose.yaml -f compose.demo.yaml exec web node /app/verify-mvp.mjs
```

An invalid source, conflicting marker/digest, unrelated target, Standard target,
failed migration, invalid descriptor/reference, or partial installation fails
closed without hidden reinstall or reset.

Bundled Demo source and descriptor are version 3. Any earlier installed dataset
conflicts deliberately: startup does not rewrite, reseed, or replace it. The
Founder must use the exact Demo-only reset below. Demo v3 seeds one isolated
portfolio review as `awaiting_decision`; exact replay preserves a later valid
human decision and never touches Standard. The Demo create loader is browser
prefill only and never auto-submits or records a decision.

Demo v3 also creates one synthetic Paper Account only through the existing
application service. Its immutable ledger contains account creation, one cash
deposit, one explicit opening-position adjustment, freeze, and reactivation.
The installer records one immutable snapshot and one matched reconciliation,
then independently replays the ledger and verifies the persisted projection and
both evidence rows. Restart repeats the idempotent commands and evidence
operations and requires exact replay. It does not create orders, fills,
execution, PnL, equity, market data, or a second financial authority.

Reset only disposable Demo storage:

```powershell
docker compose -f compose.yaml -f compose.demo.yaml down --volumes
docker compose -f compose.yaml -f compose.demo.yaml up --build --detach
```

Return to the preserved Standard workspace:

```powershell
docker compose -f compose.yaml -f compose.demo.yaml down
docker compose up --detach
docker compose exec backend el-psy-quant verify-local-workspace --mode standard --workspace-root /data
```

The original Standard database and artifacts must remain unchanged.

## Sprint 187 Existing-Volume Recovery and Acceptance

Before moving a reviewed Standard volume from `0006_portfolio_reviews` to
`0007_paper_account_ledger`, retain a cold copy of the complete stopped `/data`
tree and its recorded source commit/revision. Startup must add only the approved
Paper Account tables, indexes, constraints, and triggers. Existing research,
evidence, Paper Job, result-reference, and portfolio-review rows and files must
remain unchanged. The upgrade seeds no Standard Paper Account.

After the reviewed image starts, use only the read-only verifier and browser
reads to confirm the existing workspace. Create or mutate a Standard Paper
Account only through an explicit Founder Web/API action. Restart without
deleting the Standard volume and confirm account identity, immutable ledger
events/postings, ledger-derived detail, snapshot, and reconciliation evidence
persist exactly.

For Demo acceptance, reset only the disposable earlier-version Demo volume,
start Demo v3, and confirm:

```text
descriptor v3 and the synthetic account identity are visible
  -> list/detail show the seeded account at exact version 5
  -> ledger shows the five ordered immutable event types
  -> cash and position values match ledger replay
  -> projection status is current
  -> installer verification found the immutable snapshot
  -> reconciliation is matched and anchored to the same projection digest
  -> restart preserves and exactly replays all account/evidence identities
  -> an explicit Founder mutation persists across another restart
  -> return to Standard shows the preserved Standard workspace unchanged
```

If any replay, projection, snapshot, reconciliation, schema, or descriptor check
fails, startup refuses service. Do not rebuild a projection, edit ledger rows,
stamp Alembic, selectively restore files, or reinstall over the failed
workspace. Preserve the volume and bounded logs for diagnosis. Recovery
validation is intentionally non-repairing.

## Restore Limitations

The repository intentionally provides no automatic or destructive Standard
restore helper. A raw local backup is not a production disaster-recovery
system.

Restore only into a newly provisioned, reviewed, empty Standard volume/workspace
while its backend is stopped. Copy the complete versioned backup set together;
do not merge it with or overwrite an active non-empty Standard volume. Confirm
the recorded source commit and revision are supported, run
`verify-local-workspace` read-only before serving, and retain the original
backup until Founder acceptance completes.

If a separate empty restore target cannot be established and reviewed, stop:
do not repurpose the active Standard volume. Demo data is disposable and should
normally be reinstalled from the committed source rather than backed up or
restored.

## Responsibility Split

Codex owns deterministic repository tests, the complete
`uv run python scripts/check.py` gate, and non-starting static Compose
configuration checks. Codex does not build images, start or stop stacks, run
container health/smoke acceptance, copy live data, or remove volumes.

The Founder owns cold backup execution, Docker builds, fresh and existing-volume
startup, post-upgrade verification, bilingual runtime smoke, Demo replay/reset,
return to Standard, browser acceptance, external backup security, and the merge
decision.
