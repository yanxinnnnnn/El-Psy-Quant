import { render, screen, waitFor } from "@/test/render";
import userEvent from "@testing-library/user-event";
import { useCallback } from "react";
import { describe, expect, it, vi } from "vitest";

import type { ApiResult } from "@/lib/api-client";
import { useApiResource } from "@/lib/use-api-resource";

function deferred<Data>() {
  let resolve!: (value: ApiResult<Data>) => void;
  const promise = new Promise<ApiResult<Data>>((resolvePromise) => {
    resolve = resolvePromise;
  });
  return { promise, resolve };
}

function ResourceHarness({
  request,
}: {
  request: () => Promise<ApiResult<string>>;
}) {
  const stableRequest = useCallback(() => request(), [request]);
  const { state, retry } = useApiResource(stableRequest);
  return (
    <div>
      <output>{state.status === "success" ? state.data : state.status}</output>
      <button type="button" onClick={retry}>Refresh read</button>
    </div>
  );
}

describe("useApiResource explicit refresh sequencing", () => {
  it("prevents an older response from overwriting a newer explicit refresh", async () => {
    const first = deferred<string>();
    const second = deferred<string>();
    const request = vi
      .fn<() => Promise<ApiResult<string>>>()
      .mockReturnValueOnce(first.promise)
      .mockReturnValueOnce(second.promise);
    const user = userEvent.setup();

    render(<ResourceHarness request={request} />);
    await waitFor(() => expect(request).toHaveBeenCalledTimes(1));

    await user.click(screen.getByRole("button", { name: "Refresh read" }));
    expect(request).toHaveBeenCalledTimes(2);
    second.resolve({ data: "newer", requestId: "request-newer" });
    expect(await screen.findByText("newer")).toBeVisible();

    first.resolve({ data: "older", requestId: "request-older" });
    await waitFor(() => expect(screen.getByText("newer")).toBeVisible());
    expect(screen.queryByText("older")).not.toBeInTheDocument();
  });
});
