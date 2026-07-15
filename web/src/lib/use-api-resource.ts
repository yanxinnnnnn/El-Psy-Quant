"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { ApiClientError, type ApiResult } from "@/lib/api-client";

export type ApiResourceState<Data> =
  | { status: "loading" }
  | { status: "success"; data: Data; requestId: string | null }
  | { status: "error"; message: string; requestId: string | null; code: string };

export function useApiResource<Data>(
  request: () => Promise<ApiResult<Data>>,
): { state: ApiResourceState<Data>; retry: () => void } {
  const [state, setState] = useState<ApiResourceState<Data>>({ status: "loading" });
  const requestSequence = useRef(0);

  const load = useCallback(() => {
    const sequence = ++requestSequence.current;
    setState({ status: "loading" });
    void request()
      .then((result) => {
        if (sequence === requestSequence.current) {
          setState({
            status: "success",
            data: result.data,
            requestId: result.requestId,
          });
        }
      })
      .catch((error: unknown) => {
        if (sequence !== requestSequence.current) {
          return;
        }
        if (error instanceof ApiClientError) {
          setState({
            status: "error",
            message: error.publicMessage,
            requestId: error.requestId,
            code: error.code,
          });
          return;
        }
        setState({
          status: "error",
          message: "The local API is unavailable.",
          requestId: null,
          code: "api_unavailable",
        });
      });
  }, [request]);

  useEffect(() => {
    let active = true;
    queueMicrotask(() => {
      if (active) {
        load();
      }
    });
    return () => {
      active = false;
      requestSequence.current += 1;
    };
  }, [load]);

  return { state, retry: load };
}
