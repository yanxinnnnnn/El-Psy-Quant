# Portfolio Records

Portfolio Records provides read-only inspection of authoritative results from
succeeded paper jobs.

## Open a Result

Open **Portfolio Records**. The list contains succeeded jobs and shows whether a
result is available. Only a job with **Result available: Yes** can be opened as
a result. Use the manual **Refresh** action when you expect availability to have
changed.

You can also follow the Portfolio Record link from a succeeded Paper Job.

## Read the Result in Order

1. **Identity and result reference** confirms the job, run, schemas, timestamps,
   and provenance.
2. **Account and cash snapshots** shows the starting and ending states supplied
   by the result.
3. **Backend session summary** shows session timestamps, starting and ending
   cash, backend-provided cash change, and order/fill counts.
4. **Positions** and **Position changes** show quantities in the returned order.
5. **Orders** and **Fills** show the complete paper records in artifact order.
6. **Backend result audit** shows a separate validated summary and its counts.

The workspace preserves every returned row, including duplicates. Do not assume
that repeated rows were deduplicated or reconciled.

## Cash Is Not Total Equity

The current result provides cash and position quantities. It does not provide
current market prices for open positions, total marked-to-market equity, or an
equity history.

Therefore:

- account cash is not portfolio value;
- cash change is not automatically profit, loss, or return;
- a position quantity is not market exposure or valuation; and
- the absence of a chart is not evidence of a flat equity curve.

The session summary and result audit are displayed independently. If values
appear surprising, inspect the source identity, order/fill rows, and audit rather
than calculating a replacement value in the browser.

## Review Questions

Before comparing or making a lifecycle decision, ask whether the intended run
was opened, timestamps are plausible, starting and ending states match the
review scenario, orders and fills are internally understandable, and warnings or
missing rows require follow-up.
