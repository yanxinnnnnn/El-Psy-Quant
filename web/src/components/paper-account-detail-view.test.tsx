import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { PaperAccountDetailView } from "@/components/paper-account-detail-view";
import { render, screen, within } from "@/test/render";
import {
  paperAccountCommand,
  paperAccountDetail,
  paperAccountLedger,
  paperAccountReconciliation,
  paperAccountSnapshot,
} from "@/test/paper-account-fixtures";

afterEach(() => vi.unstubAllGlobals());

function response(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json",
      "X-Request-ID": "paper-detail-request",
    },
  });
}

describe("Founder Paper Account detail workspace", () => {
  it("renders complete backend projection, approved evidence, and ledger postings without PnL or equity calculation", async () => {
    const fetcher = vi.fn<typeof fetch>()
      .mockResolvedValueOnce(response(paperAccountDetail))
      .mockResolvedValueOnce(response(paperAccountLedger));
    vi.stubGlobal("fetch", fetcher);
    render(<PaperAccountDetailView accountId="paper-account-186" />);

    for (const heading of [
      "Account authority",
      "Current backend projection",
      "Immutable ledger timeline",
      "Explicit account operations",
      "Snapshot and reconciliation evidence",
    ]) {
      expect(await screen.findByRole("heading", { name: heading })).toBeVisible();
    }
    expect(screen.getAllByText("1234.56789")[0]).toBeVisible();
    expect(screen.getByText("3.25")).toBeVisible();
    expect(screen.getByText("456.789")).toBeVisible();
    expect(screen.getByText("140.55046154")).toBeVisible();
    expect(screen.getByRole("link", {
      name: "Inspect governance review",
    })).toHaveAttribute(
      "href",
      "/portfolio-reviews/review-approved-186",
    );
    expect(screen.getByText("cash-deposit-186")).toBeInTheDocument();
    expect(screen.getAllByText("234.56789").length).toBeGreaterThan(0);
    expect(screen.queryByRole("heading", { name: /PnL/i }))
      .not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: /equity/i }))
      .not.toBeInTheDocument();
  });

  it("submits exact cash input with the displayed backend version and preserves the accepted event", async () => {
    const fetcher = vi.fn<typeof fetch>()
      .mockResolvedValueOnce(response(paperAccountDetail))
      .mockResolvedValueOnce(response(paperAccountLedger))
      .mockResolvedValueOnce(response(paperAccountCommand, 201));
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<PaperAccountDetailView accountId="paper-account-186" />);
    const group = await screen.findByRole("group", { name: "Cash movement" });

    expect(within(group).getByLabelText("Expected account version"))
      .toHaveValue("2");
    await user.selectOptions(
      within(group).getByLabelText("Movement type"),
      "deposit",
    );
    await user.type(
      within(group).getByLabelText("Requested amount"),
      "12.34567",
    );
    await user.type(
      within(group).getByLabelText("Effective timestamp UTC (optional)"),
      "2026-07-26T12:00:00Z",
    );
    await user.type(within(group).getByLabelText("Actor"), "founder");
    await user.type(within(group).getByLabelText("Reason"), "Explicit deposit");
    await user.type(
      within(group).getByLabelText("Idempotency-Key"),
      "Cash:Detail:186",
    );
    await user.click(screen.getByRole("button", {
      name: "Submit cash movement",
    }));

    expect(await screen.findByRole("heading", {
      name: "Backend accepted the account operation",
    })).toBeVisible();
    expect(fetcher.mock.calls[2][0]).toBe(
      "/api/backend/api/v1/paper-accounts/paper-account-186/cash-movements",
    );
    expect(JSON.parse(String(fetcher.mock.calls[2][1]?.body))).toEqual({
      expected_account_version: 2,
      actor: "founder",
      reason: "Explicit deposit",
      movement_type: "deposit",
      requested_amount: "12.34567",
      effective_timestamp_utc: "2026-07-26T12:00:00Z",
    });
    expect(fetcher.mock.calls[2][1]?.headers).toMatchObject({
      "Idempotency-Key": "Cash:Detail:186",
    });
    expect(screen.getAllByText("event-cash-186").length).toBeGreaterThan(0);
  });

  it("uses exact current anchors and inspects immutable snapshot and reconciliation responses", async () => {
    const fetcher = vi.fn<typeof fetch>()
      .mockResolvedValueOnce(response(paperAccountDetail))
      .mockResolvedValueOnce(response(paperAccountLedger))
      .mockResolvedValueOnce(response(paperAccountSnapshot, 201))
      .mockResolvedValueOnce(response(paperAccountReconciliation, 201));
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<PaperAccountDetailView accountId="paper-account-186" />);
    const snapshot = await screen.findByRole("group", {
      name: "Create snapshot",
    });
    expect(within(snapshot).getByLabelText("Expected account version"))
      .toHaveValue("2");
    expect(within(snapshot).getByLabelText("Expected head event ID"))
      .toHaveValue("event-cash-186");
    expect(within(snapshot).getByLabelText("Expected head chain digest"))
      .toHaveValue("b".repeat(64));
    await user.type(within(snapshot).getByLabelText("Actor"), "founder");
    await user.type(within(snapshot).getByLabelText("Reason"), "Snapshot reason");
    await user.type(
      within(snapshot).getByLabelText("Idempotency-Key"),
      "Snapshot:Detail:186",
    );
    await user.click(screen.getByRole("button", { name: "Create snapshot" }));
    expect(await screen.findByRole("heading", {
      name: "Immutable snapshot inspection",
    })).toBeVisible();
    expect(screen.getByText("snapshot-186")).toBeVisible();

    const reconciliation = screen.getByRole("group", {
      name: "Create reconciliation",
    });
    await user.type(within(reconciliation).getByLabelText("Actor"), "founder");
    await user.type(
      within(reconciliation).getByLabelText("Reason"),
      "Reconciliation reason",
    );
    await user.type(
      within(reconciliation).getByLabelText("Idempotency-Key"),
      "Reconciliation:Detail:186",
    );
    await user.click(screen.getByRole("button", {
      name: "Create reconciliation",
    }));
    expect(await screen.findByRole("heading", {
      name: "Immutable reconciliation inspection",
    })).toBeVisible();
    expect(screen.getByText("reconciliation-186")).toBeVisible();
    expect(screen.getAllByText("matched").length).toBeGreaterThan(0);
    expect(JSON.parse(String(fetcher.mock.calls[3][1]?.body))).toEqual({
      expected_account_version: 2,
      expected_head_event_id: "event-cash-186",
      expected_head_chain_digest: "b".repeat(64),
      actor: "founder",
      reason: "Reconciliation reason",
    });
  });

  it("preserves operation drafts after backend version conflict", async () => {
    const fetcher = vi.fn<typeof fetch>()
      .mockResolvedValueOnce(response(paperAccountDetail))
      .mockResolvedValueOnce(response(paperAccountLedger))
      .mockResolvedValueOnce(response({
        error: {
          code: "paper_account_version_conflict",
          message: "Safe version conflict",
        },
        request_id: "paper-version-conflict",
      }, 409));
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<PaperAccountDetailView accountId="paper-account-186" />);
    const group = await screen.findByRole("group", {
      name: "Link approved M30 evidence",
    });
    await user.type(
      within(group).getByLabelText("Approved portfolio review ID"),
      "preserved-review",
    );
    await user.type(within(group).getByLabelText("Actor"), "founder");
    await user.type(within(group).getByLabelText("Reason"), "Preserved reason");
    await user.type(
      within(group).getByLabelText("Idempotency-Key"),
      "Evidence:Conflict:186",
    );
    await user.click(screen.getByRole("button", {
      name: "Link approved evidence",
    }));

    expect(await screen.findByRole("heading", {
      name: "Paper Account version changed",
    })).toBeVisible();
    expect(within(group).getByLabelText("Approved portfolio review ID"))
      .toHaveValue("preserved-review");
    expect(within(group).getByLabelText("Reason"))
      .toHaveValue("Preserved reason");
    expect(within(group).getByLabelText("Idempotency-Key"))
      .toHaveValue("Evidence:Conflict:186");
  });
});
