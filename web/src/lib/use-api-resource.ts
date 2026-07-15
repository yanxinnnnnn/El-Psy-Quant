"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { ApiClientError, type ApiResult } from "@/lib/api-client";

export type ApiResourceState<Data> =
  | { status: "loading"; sequence: number }
  | { status: "success"; data: Data; requestId: string | null; sequence: number }
  | { status: "error"; message: string; requestId: string | null; code: string; sequence: number };

export function useApiResource<Data>(
  request: () => Promise<ApiResult<Data>>,
): { state: ApiResourceState<Data>; retry: () => number } {
  const [state, setState] = useState<ApiResourceState<Data>>({ status: "loading", sequence: 0 });
  const requestSequence = useRef(0);

  const load = useCallback(() => {
    const sequence = ++requestSequence.current;
    setState({ status: "loading", sequence });
    void request()
      .then((result) => {
        if (sequence === requestSequence.current) {
          setState({
            status: "success",
            data: result.data,
            requestId: result.requestId,
            sequence,
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
            sequence,
          });
          return;
        }
        setState({
          status: "error",
          message: "The local API is unavailable.",
          requestId: null,
          code: "api_unavailable",
          sequence,
        });
      });
    return sequence;
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
