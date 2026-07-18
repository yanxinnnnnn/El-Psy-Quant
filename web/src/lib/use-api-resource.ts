"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { ApiClientError, type ApiResult } from "@/lib/api-client";

export type SettledApiResourceState<Data> =
  | { status: "success"; data: Data; requestId: string | null; sequence: number }
  | {
      status: "error";
      message: string;
      requestId: string | null;
      code: string;
      httpStatus: number | null;
      sequence: number;
    };

export type ApiResourceState<Data> =
  | {
      status: "loading";
      sequence: number;
      previous: SettledApiResourceState<Data> | null;
    }
  | SettledApiResourceState<Data>;

export function useApiResource<Data>(
  request: () => Promise<ApiResult<Data>>,
): { state: ApiResourceState<Data>; retry: () => number } {
  const [state, setState] = useState<ApiResourceState<Data>>({
    status: "loading",
    sequence: 0,
    previous: null,
  });
  const requestSequence = useRef(0);

  const load = useCallback(() => {
    const sequence = ++requestSequence.current;
    setState((current) => ({
      status: "loading",
      sequence,
      previous: current.status === "loading" ? current.previous : current,
    }));
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
            httpStatus: error.status > 0 ? error.status : null,
            sequence,
          });
          return;
        }
        setState({
          status: "error",
          message: "The local API is unavailable.",
          requestId: null,
          code: "api_unavailable",
          httpStatus: null,
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
