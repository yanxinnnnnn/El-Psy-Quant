# Founder Demo Workspace

This directory is the versioned, deterministic source for the **demo-only**
Founder workspace. It is installed only by the explicit backend/operator demo
installer into isolated demo storage.

The dataset uses the registered `moving_average_crossover` strategy and links
one review journey across saved research evidence, governance/report manifests,
two completed paper-result chains, comparison candidates, and stateless
lifecycle review examples. Dataset/descriptor v5 also supplies one exact
portfolio-review create request. Installation uses existing domain/application
authority to seed one isolated `awaiting_decision` review; it does not seed a
decision, and exact replay preserves a later valid Founder decision.

Demo v5 also uses the existing Paper Account application service to seed one
deterministic account journey with immutable cash and position postings,
freeze/reactivate events, one immutable snapshot, and one matched
reconciliation. Ledger replay remains state authority; the descriptor and Demo
source are presentation and verification inputs only. The position adjustment
is an explicit synthetic opening balance, not an order, fill, execution, PnL,
equity, or capital recommendation. It contains no credentials, network dependency,
profitability claim, suitability claim, live-readiness claim, or automatic
approval.

Demo v5 additionally supplies one immutable XNYS calendar, two ordered sessions,
five canonical market-data events, and one paused replay checkpoint after four
same-instrument trades. Installation
uses only the existing market-time domain and persistence authorities. Restart
verification restores the exact stream and cursor, consumes the remaining two
events in memory to prove deterministic completion, and confirms that validation
did not change the durable paused checkpoint.

The installer then invokes only `StrategyOrderApplicationService` to create one
deterministic Signal, one account-bound buy Intent, one allow Decision, and one
maximum-quantity reject Decision. Exact receipts prove replay after restart.
The descriptor merely exposes discovery metadata; verification strictly reads
and reconstructs the persisted authority and never reruns commands, repairs
rows, advances replay, or mutates the Paper Account. This fixture never creates
or mutates execution orders, fills, reservations, or financial authority.

Do not copy these files into a standard workspace. Use the documented demo
Compose workflow or the `install-demo-workspace` operator command.
