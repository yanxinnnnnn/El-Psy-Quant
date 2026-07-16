import userEvent from "@testing-library/user-event";
import { usePathname, useSearchParams } from "next/navigation";
import { afterEach, describe, expect, it, vi } from "vitest";

import { LanguageSwitcher } from "@/components/language-switcher";
import { LifecycleReviewWorkspace } from "@/components/lifecycle-review-workspace";
import { PaperJobSubmissionView } from "@/components/paper-job-submission-view";
import { render, screen, waitFor } from "@/test/render";

const navigation = vi.hoisted(() => ({
  pathname: "/comparisons",
  search: new URLSearchParams("job_id=job-a&job_id=job-b&job_id=job-a"),
  refresh: vi.fn(),
  push: vi.fn(),
  replace: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  usePathname: () => navigation.pathname,
  useSearchParams: () => navigation.search,
  useRouter: () => ({
    refresh: navigation.refresh,
    push: navigation.push,
    replace: navigation.replace,
  }),
}));

function CurrentLocation() {
  const pathname = usePathname();
  const search = useSearchParams();
  return <output>{`${pathname}?${search.toString()}`}</output>;
}

afterEach(() => {
  vi.unstubAllGlobals();
  navigation.refresh.mockReset();
  navigation.push.mockReset();
  navigation.replace.mockReset();
});

function localeResponse() {
  return Promise.resolve(new Response(JSON.stringify({ locale: "zh-CN" }), {
    status: 200,
    headers: { "content-type": "application/json" },
  }));
}

describe("LanguageSwitcher", () => {
  it("is accessible and changes locale without navigating or rewriting repeated query values", async () => {
    const fetcher = vi.fn<typeof fetch>().mockImplementation(localeResponse);
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<><LanguageSwitcher /><CurrentLocation /></>);

    const english = screen.getByRole("button", { name: "Switch language to English" });
    const chinese = screen.getByRole("button", { name: "Switch language to 简体中文" });
    expect(english).toHaveAttribute("aria-pressed", "true");
    expect(chinese).toHaveAttribute("aria-pressed", "false");
    expect(screen.getByText("/comparisons?job_id=job-a&job_id=job-b&job_id=job-a")).toBeVisible();

    await user.click(chinese);
    await waitFor(() => expect(navigation.refresh).toHaveBeenCalledOnce());
    expect(fetcher).toHaveBeenCalledWith("/api/locale", expect.objectContaining({
      method: "POST",
      body: JSON.stringify({ locale: "zh-CN" }),
    }));
    expect(navigation.push).not.toHaveBeenCalled();
    expect(navigation.replace).not.toHaveBeenCalled();
    expect(screen.getByText("/comparisons?job_id=job-a&job_id=job-b&job_id=job-a")).toBeVisible();
  });

  it("preserves an in-progress paper submission while refreshing translated server content", async () => {
    vi.stubGlobal("fetch", vi.fn<typeof fetch>().mockImplementation(localeResponse));
    const user = userEvent.setup();
    render(<><LanguageSwitcher /><PaperJobSubmissionView /></>);
    const runId = screen.getByLabelText("Run ID");
    await user.type(runId, "founder-unsubmitted-run");
    await user.click(screen.getByRole("button", { name: "Switch language to 简体中文" }));
    await waitFor(() => expect(navigation.refresh).toHaveBeenCalledOnce());
    expect(runId).toHaveValue("founder-unsubmitted-run");
    expect(navigation.push).not.toHaveBeenCalled();
  });

  it("preserves an in-progress lifecycle proposal and triggers no command", async () => {
    const fetcher = vi.fn<typeof fetch>().mockImplementation(localeResponse);
    vi.stubGlobal("fetch", fetcher);
    const user = userEvent.setup();
    render(<><LanguageSwitcher /><LifecycleReviewWorkspace /></>);
    const proposalId = screen.getByLabelText("Proposal ID");
    await user.type(proposalId, "proposal-not-submitted");
    await user.click(screen.getByRole("button", { name: "Switch language to 简体中文" }));
    await waitFor(() => expect(navigation.refresh).toHaveBeenCalledOnce());
    expect(proposalId).toHaveValue("proposal-not-submitted");
    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(navigation.push).not.toHaveBeenCalled();
  });
});
