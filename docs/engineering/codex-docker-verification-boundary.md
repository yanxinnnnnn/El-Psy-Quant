# Codex Docker Verification Boundary

## Decision

For future El-Psy-Quant implementation sprints, Codex does not perform Docker
runtime acceptance.

Codex must not attempt:

```text
docker compose build
docker compose up
container startup
container-based smoke verification
```

This rule also covers equivalent commands that pull/build images or start the
local Standard or Demo product stack.

## Reason

Docker runtime acceptance is a Founder-owned product-acceptance responsibility,
separate from implementation verification. Image builds and container startup
also depend on machine-local state and external dependency availability that are
outside repository authority.

VPN, proxy, DNS, and other network settings are machine environment. Codex must
not assume a particular provider, endpoint, port, environment variable, or
network topology. A transient network/dependency failure should be reported as
observed; it must not be worked around by adding repository proxy settings or by
changing unrelated project files.

## Codex Responsibilities

Codex must:

- implement the authoritative GitHub Issue;
- add deterministic tests;
- run the full repository quality gate:

```text
uv run python scripts/check.py
```

- run non-starting static configuration checks when required, for example:

```text
docker compose config
docker compose -f compose.yaml -f compose.demo.yaml config
```

- report all verification results truthfully;
- state that Docker build/start was intentionally not attempted under project
  policy; and
- open a Ready-for-review PR without merging it.

Static Compose checks are allowed because they validate effective configuration
without building images, pulling dependencies, starting containers, or relying
on product runtime availability.

## Founder Responsibilities

The Founder performs local runtime acceptance after reviewing the implementation
PR or after switching to its branch.

Runtime acceptance may include:

- Docker image build;
- Standard workspace startup;
- Demo workspace startup;
- container health inspection;
- container-based smoke verification;
- browser workflow verification;
- Standard/Demo storage-isolation verification; and
- final product-experience acceptance.

The Founder decides whether runtime acceptance is sufficient for merge.

## PR Reporting Contract

Every Codex PR whose behavior affects Docker/local startup must include a section
similar to:

```text
Docker runtime acceptance

- Not attempted by Codex under project policy.
- Static Compose configuration checks: passed / not applicable.
- Local build, startup, and browser acceptance remain for the Founder.
```

Codex must not describe the missing Docker runtime step as an environment
failure unless it accidentally attempted it. The expected state is “not
attempted by policy.”

## Definition of Done Impact

A Codex implementation is eligible for CTO review when:

- the authoritative Issue is implemented;
- `uv run python scripts/check.py` passes;
- applicable static configuration checks pass;
- documentation is updated;
- the PR is Ready for review; and
- Docker runtime acceptance is explicitly handed to the Founder.

A successful Docker build/start is not required from Codex.

## Exceptions

An exception requires an explicit Founder instruction in the current sprint.
The CTO must not silently add Docker build/start back into a future Codex prompt
or Issue acceptance criteria.
