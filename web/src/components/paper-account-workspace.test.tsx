import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { PaperAccountCreateView } from "@/components/paper-account-create-view";
import { PaperAccountListView } from "@/components/paper-account-list-view";
import { render, screen, waitFor } from "@/test/render";
import {
  paperAccountCommand,
  paperAccountList,
} from "@/test/paper-account-fixtures";

vi.mock("next/navigation", () => ({
  usePathname: () => "/paper-accounts",
  useRouter: () => ({ refresh: vi.fn() }),
}));

afterEach(() => vi.unstubAllGlobals());

function response(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json",
      "X-Request-ID": "paper-workspace-request",
    },
  });
}

describe("Founder Paper Account list and create workspace", () => {
  it("renders backend list order and performs explicit opaque-cursor pagination", async () => {
    const nextPage = {
      ...paperAccountList,
      items: [{
        ...paperAccountList.items[0],
        account_id: "paper-account-next",
        display_name: "Next Account",
      }],
      next_cursor: null,
    };
    const fetcher = vi.fn<typeof fetch>()
      .mockResolvedValueOnce(response(paperAccountList))
      .mockResolvedValueOnce(response(nextPage));
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();

    render(<PaperAccountListView />);
    expect(await screen.findByRole("heading", {
      name: "Founder Paper Account",
    })).toBeVisible();
    expect(screen.queryByText("1234.56789")).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Inspect account" }))
      .toHaveAttribute("href", "/paper-accounts/paper-account-186");
    await user.click(screen.getByRole("button", { name: "Next page" }));
    expect(await screen.findByRole("heading", {
      name: "Next Account",
    })).toBeVisible();
    expect(fetcher.mock.calls[1][0]).toBe(
      "/api/backend/api/v1/paper-accounts?limit=50&cursor=opaque-next-cursor",
    );
  });

  it("submits exact creation strings and keeps navigation explicit", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
      response(paperAccountCommand, 201),
    );
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<PaperAccountCreateView />);

    await user.type(screen.getByLabelText("Display name"), "Founder Account 186");
    await user.type(
      screen.getByLabelText("Base currency (three letters)"),
      "USD",
    );
    await user.type(screen.getByLabelText(/^Initial cash/), "1000.25");
    await user.type(screen.getByLabelText("Actor"), "founder");
    await user.type(screen.getByLabelText("Idempotency-Key"), "Create:186");
    await user.click(screen.getByRole("checkbox"));
    await user.click(screen.getByRole("button", {
      name: "Create Paper Account",
    }));

    expect(await screen.findByRole("heading", {
      name: "Paper Account created",
    })).toBeVisible();
    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(fetcher.mock.calls[0][1]?.headers).toMatchObject({
      "Idempotency-Key": "Create:186",
    });
    expect(JSON.parse(String(fetcher.mock.calls[0][1]?.body))).toEqual({
      display_name: "Founder Account 186",
      base_currency: "USD",
      initial_cash: "1000.25",
      actor: "founder",
    });
    expect(screen.getByRole("link", {
      name: "Inspect authoritative account detail",
    })).toHaveAttribute("href", "/paper-accounts/paper-account-186");
  });

  it("preserves invalid drafts and sends no request", async () => {
    const fetcher = vi.fn<typeof fetch>();
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<PaperAccountCreateView />);
    await user.type(screen.getByLabelText("Display name"), "Preserved draft");
    await user.type(
      screen.getByLabelText("Base currency (three letters)"),
      "USD",
    );
    await user.type(screen.getByLabelText(/^Initial cash/), "1e3");
    await user.type(screen.getByLabelText("Actor"), "founder");
    await user.type(screen.getByLabelText("Idempotency-Key"), "Invalid:186");
    await user.click(screen.getByRole("checkbox"));
    await user.click(screen.getByRole("button", {
      name: "Create Paper Account",
    }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "No request was sent",
    );
    expect(screen.getByLabelText("Display name")).toHaveValue("Preserved draft");
    expect(screen.getByLabelText(/^Initial cash/)).toHaveValue("1e3");
    expect(fetcher).not.toHaveBeenCalled();
  });

  it("renders Simplified Chinese copy while preserving raw backend truth", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn<typeof fetch>().mockResolvedValue(response(paperAccountList)),
    );
    render(<PaperAccountListView />, { locale: "zh-CN" });

    expect(await screen.findByRole("heading", {
      name: "模拟账户",
    })).toBeVisible();
    expect(screen.getByText("Founder Paper Account")).toBeVisible();
    expect(screen.getByText("paper-account-186")).toBeVisible();
    await waitFor(() => {
      expect(screen.getByText("active")).toBeVisible();
    });
  });
});
