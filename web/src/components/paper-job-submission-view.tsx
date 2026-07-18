"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { useRef, useState } from "react";

import { ErrorState, RequestId } from "@/components/data-states";
import { PaperJobStatusValue } from "@/components/domain-values";
import {
  ApiClientError,
  fetchDemoWorkspace,
  submitPaperJob,
  type DemoWorkspaceDescriptorResponse,
  type PaperJobSubmissionRequest,
  type PaperJobSubmissionResponse,
} from "@/lib/api-client";

type PositionRow = { key: number; symbol: string; quantity: string };
type AccountInput = {
  timestamp: string;
  startingCash: string;
  currentCash: string;
  positions: PositionRow[];
};
type OrderRow = {
  key: number;
  orderId: string;
  timestamp: string;
  symbol: string;
  side: string;
  quantity: string;
  status: string;
};
type FillRow = {
  key: number;
  timestamp: string;
  symbol: string;
  side: string;
  quantity: string;
  price: string;
  orderId: string;
};
type FieldErrors = Record<string, string>;

const decimalTransportPattern = /^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$/;

function parseNumericTransportValue(value: string): number | null {
  if (!decimalTransportPattern.test(value)) {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

const blankAccount = (): AccountInput => ({
  timestamp: "",
  startingCash: "",
  currentCash: "",
  positions: [],
});

function FieldError({ id, message }: { id: string; message?: string }) {
  return message ? <span className="field-error" id={id}>{message}</span> : null;
}

function fieldA11y(errors: FieldErrors, name: string) {
  return {
    "aria-invalid": errors[name] ? true : undefined,
    "aria-describedby": errors[name] ? `${name}-error` : undefined,
  };
}

function AccountSection({
  legend,
  prefix,
  value,
  setValue,
  errors,
  nextKey,
}: {
  legend: string;
  prefix: "starting" | "ending";
  value: AccountInput;
  setValue: (value: AccountInput) => void;
  errors: FieldErrors;
  nextKey: () => number;
}) {
  const t = useTranslations("paperJobs.submission");
  const update = (field: keyof Omit<AccountInput, "positions">, next: string) =>
    setValue({ ...value, [field]: next });
  return (
    <fieldset className="form-section">
      <legend>{legend}</legend>
      <p className="form-section__description">{t("accountDescription")}</p>
      <div className="form-grid">
        {[
          ["timestamp", t("accountTimestamp"), value.timestamp, "2026-01-18T13:55:00Z", t("timestampGuidance")],
          ["startingCash", t("startingCash"), value.startingCash, "50000.00", t("nonNegativeGuidance")],
          ["currentCash", t("currentCash"), value.currentCash, "50000.00", t("nonNegativeGuidance")],
        ].map(([field, label, current, placeholder, guidance]) => {
          const name = `${prefix}-${field}`;
          const numeric = field !== "timestamp";
          return (
            <label key={field}>
              {label} <span className="required-label">{t("required")}</span>
              <input
                id={name}
                name={name}
                aria-label={field === "timestamp" ? t("timestamp") : label}
                required
                inputMode={numeric ? "decimal" : undefined}
                placeholder={placeholder}
                value={current}
                onChange={(event) => update(field as "timestamp" | "startingCash" | "currentCash", event.target.value)}
                {...fieldA11y(errors, name)}
              />
              <span className="field-guidance">{guidance}</span>
              <FieldError id={`${name}-error`} message={errors[name]} />
            </label>
          );
        })}
      </div>
      <div className="repeatable-heading">
        <div><h3>{t("positions")}</h3><p>{t("positionsDescription")}</p></div>
        <button
          className="secondary-button"
          type="button"
          onClick={() => setValue({ ...value, positions: [...value.positions, { key: nextKey(), symbol: "", quantity: "" }] })}
        >
          {t("addPosition")}
        </button>
      </div>
      {value.positions.length === 0 ? <p className="repeatable-empty">{t("noPositions")}</p> : (
        <div className="repeatable-list">
          {value.positions.map((position, index) => {
            const symbolName = `${prefix}-position-${index}-symbol`;
            const quantityName = `${prefix}-position-${index}-quantity`;
            return (
              <div className="repeatable-row repeatable-row--position" key={position.key}>
                <span className="row-number">{t("positionNumber", { number: index + 1 })}</span>
                <label>{t("symbol")} <span className="required-label">{t("required")}</span><input aria-label={t("symbol")} placeholder="AAPL" value={position.symbol} onChange={(event) => setValue({ ...value, positions: value.positions.map((row) => row.key === position.key ? { ...row, symbol: event.target.value } : row) })} {...fieldA11y(errors, symbolName)} /><FieldError id={`${symbolName}-error`} message={errors[symbolName]} /></label>
                <label>{t("quantity")} <span className="required-label">{t("required")}</span><input aria-label={t("quantity")} inputMode="decimal" placeholder="10" value={position.quantity} onChange={(event) => setValue({ ...value, positions: value.positions.map((row) => row.key === position.key ? { ...row, quantity: event.target.value } : row) })} {...fieldA11y(errors, quantityName)} /><span className="field-guidance">{t("quantityGuidance")}</span><FieldError id={`${quantityName}-error`} message={errors[quantityName]} /></label>
                <button className="remove-button" type="button" onClick={() => setValue({ ...value, positions: value.positions.filter((row) => row.key !== position.key) })}>{t("removePosition", { number: index + 1 })}</button>
              </div>
            );
          })}
        </div>
      )}
    </fieldset>
  );
}

export function PaperJobSubmissionView() {
  const t = useTranslations("paperJobs.submission");
  const keyCounter = useRef(0);
  const pendingRef = useRef(false);
  const [runId, setRunId] = useState("");
  const [createdTimestamp, setCreatedTimestamp] = useState("");
  const [idempotencyKey, setIdempotencyKey] = useState("");
  const [starting, setStarting] = useState(blankAccount);
  const [ending, setEnding] = useState(blankAccount);
  const [orders, setOrders] = useState<OrderRow[]>([]);
  const [fills, setFills] = useState<FillRow[]>([]);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [pending, setPending] = useState(false);
  const [serverError, setServerError] = useState<{
    code: string;
    message: string;
    requestId: string | null;
    httpStatus: number | null;
  } | null>(null);
  const [submissionResult, setSubmissionResult] = useState<{
    response: PaperJobSubmissionResponse;
    requestId: string | null;
  } | null>(null);
  const [demoLoading, setDemoLoading] = useState(false);
  const [demoDiscoveryError, setDemoDiscoveryError] = useState<string | null>(null);
  const nextKey = () => ++keyCounter.current;

  function populateDemoExample(demoDescriptor: DemoWorkspaceDescriptorResponse) {
    const example = demoDescriptor.paper_job_submission_example;
    const request = example.request;
    const accountInput = (
      account: typeof request.starting_account_state,
    ): AccountInput => ({
      timestamp: account.timestamp,
      startingCash: String(account.starting_cash),
      currentCash: String(account.current_cash),
      positions: Object.entries(account.positions).map(([symbol, quantity]) => ({
        key: nextKey(),
        symbol,
        quantity: String(quantity),
      })),
    });
    setRunId(request.run_id);
    setCreatedTimestamp(request.created_timestamp);
    setIdempotencyKey(example.idempotency_key);
    setStarting(accountInput(request.starting_account_state));
    setEnding(accountInput(request.ending_account_state));
    setOrders(request.orders.map((order) => ({
      key: nextKey(),
      orderId: order.order_id,
      timestamp: order.timestamp,
      symbol: order.symbol,
      side: order.side,
      quantity: String(order.quantity),
      status: order.status,
    })));
    setFills(request.fills.map((fill) => ({
      key: nextKey(),
      timestamp: fill.timestamp,
      symbol: fill.symbol,
      side: fill.side,
      quantity: String(fill.quantity),
      price: String(fill.price),
      orderId: fill.order_id ?? "",
    })));
    setErrors({});
    setServerError(null);
  }

  function loadDemoExample() {
    setDemoLoading(true);
    setDemoDiscoveryError(null);
    void fetchDemoWorkspace().then((result) => {
      populateDemoExample(result.data);
    }).catch((error: unknown) => {
      if (
        error instanceof ApiClientError &&
        error.code === "demo_workspace_not_configured"
      ) {
        setDemoDiscoveryError(t("demoStart"));
        return;
      }
      setDemoDiscoveryError(
        error instanceof ApiClientError
          ? error.publicMessage
          : t("demoLoadFailed"),
      );
    }).finally(() => setDemoLoading(false));
  }

  function buildRequest(): PaperJobSubmissionRequest | null {
    const nextErrors: FieldErrors = {};
    const numericValues = new Map<string, number>();
    const required = (name: string, value: string): string => {
      if (value.length === 0) nextErrors[name] = t("requiredError");
      return value;
    };
    const validateNumeric = (
      name: string,
      value: string,
      constraint: "finite" | "non-negative" | "positive" = "finite",
    ) => {
      const parsed = parseNumericTransportValue(value);
      if (parsed === null) {
        nextErrors[name] = t("numberError");
        return;
      }
      if (constraint === "non-negative" && parsed < 0) {
        nextErrors[name] = t("nonNegativeError");
        return;
      }
      if (constraint === "positive" && parsed <= 0) {
        nextErrors[name] = t("positiveError");
        return;
      }
      numericValues.set(name, parsed);
    };
    const validateAccount = (prefix: "starting" | "ending", input: AccountInput) => {
      const symbols = new Set<string>();
      input.positions.forEach((position, index) => {
        const symbolName = `${prefix}-position-${index}-symbol`;
        const quantityName = `${prefix}-position-${index}-quantity`;
        if (position.symbol.length === 0) {
          nextErrors[symbolName] = t("positionSymbolError");
        } else if (symbols.has(position.symbol)) {
          nextErrors[symbolName] = t("duplicateSymbolError");
        }
        symbols.add(position.symbol);
        validateNumeric(quantityName, position.quantity);
      });
      required(`${prefix}-timestamp`, input.timestamp);
      validateNumeric(`${prefix}-startingCash`, input.startingCash, "non-negative");
      validateNumeric(`${prefix}-currentCash`, input.currentCash, "non-negative");
    };

    required("run-id", runId);
    required("created-timestamp", createdTimestamp);
    validateAccount("starting", starting);
    validateAccount("ending", ending);
    orders.forEach((order, index) => {
      required(`order-${index}-orderId`, order.orderId);
      required(`order-${index}-timestamp`, order.timestamp);
      required(`order-${index}-symbol`, order.symbol);
      required(`order-${index}-side`, order.side);
      validateNumeric(`order-${index}-quantity`, order.quantity, "positive");
      required(`order-${index}-status`, order.status);
    });
    fills.forEach((fill, index) => {
      required(`fill-${index}-timestamp`, fill.timestamp);
      required(`fill-${index}-symbol`, fill.symbol);
      required(`fill-${index}-side`, fill.side);
      validateNumeric(`fill-${index}-quantity`, fill.quantity, "positive");
      validateNumeric(`fill-${index}-price`, fill.price, "non-negative");
    });
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) {
      return null;
    }

    const numeric = (name: string): number => {
      const value = numericValues.get(name);
      if (value === undefined) {
        throw new Error(`Missing validated numeric transport field: ${name}`);
      }
      return value;
    };
    const account = (prefix: "starting" | "ending", input: AccountInput) => ({
      timestamp: input.timestamp,
      starting_cash: numeric(`${prefix}-startingCash`),
      current_cash: numeric(`${prefix}-currentCash`),
      positions: Object.fromEntries(input.positions.map((row, index) => [
        row.symbol,
        numeric(`${prefix}-position-${index}-quantity`),
      ])),
    });
    return {
      run_id: runId,
      created_timestamp: createdTimestamp,
      starting_account_state: account("starting", starting),
      ending_account_state: account("ending", ending),
      orders: orders.map((order, index) => ({
        order_id: order.orderId,
        timestamp: order.timestamp,
        symbol: order.symbol,
        side: order.side,
        quantity: numeric(`order-${index}-quantity`),
        status: order.status,
      })),
      fills: fills.map((fill, index) => ({
        timestamp: fill.timestamp,
        symbol: fill.symbol,
        side: fill.side,
        quantity: numeric(`fill-${index}-quantity`),
        price: numeric(`fill-${index}-price`),
        order_id: fill.orderId.length === 0 ? null : fill.orderId,
      })),
    };
  }

  return (
    <div className="business-workspace">
      <div className="back-links"><Link className="text-link" href="/paper-jobs">{t("back")}</Link></div>
      <header className="page-heading page-heading--detail">
        <p className="eyebrow">{t("eyebrow")}</p>
        <h1>{t("title")}</h1>
        <p>{t("description")}</p>
      </header>

      <div className="demo-form-action">
        <button className="secondary-button" type="button" disabled={demoLoading} onClick={loadDemoExample}>
          {demoLoading ? t("loadingDemo") : t("loadDemo")}
        </button>
        <p>{t("demoDescription")}</p>
      </div>
      {demoDiscoveryError ? (
        <p className="neutral-note" role="status">{t("demoUnavailable", { message: demoDiscoveryError })}</p>
      ) : null}

      <form className="paper-job-form" noValidate onSubmit={(event) => {
        event.preventDefault();
        if (pendingRef.current) return;
        const request = buildRequest();
        if (request === null) {
          setServerError(null);
          return;
        }
        pendingRef.current = true;
        setPending(true);
        setServerError(null);
        setSubmissionResult(null);
        void submitPaperJob(request, idempotencyKey).then((result) => {
          setSubmissionResult({
            response: result.data,
            requestId: result.requestId,
          });
        }).catch((error: unknown) => {
          if (error instanceof ApiClientError) {
            setServerError({
              code: error.code,
              message: error.publicMessage,
              requestId: error.requestId,
              httpStatus: error.status > 0 ? error.status : null,
            });
          } else {
            setServerError({
              code: "api_unavailable",
              message: "The local API is unavailable.",
              requestId: null,
              httpStatus: null,
            });
          }
        }).finally(() => {
          pendingRef.current = false;
          setPending(false);
        });
      }}>
        {Object.keys(errors).length > 0 ? <div className="form-alert" role="alert"><strong>{t("attentionTitle")}</strong><span>{t("attentionDescription")}</span></div> : null}
        {serverError ? (
          <ErrorState
            className="form-alert form-alert--server"
            title={t("attentionTitle")}
            code={serverError.code}
            message={serverError.message}
            requestId={serverError.requestId}
            httpStatus={serverError.httpStatus}
            operation="paper_job.submit"
          />
        ) : null}
        {submissionResult ? (
          <div className="mutation-notice mutation-notice--success" role="status">
            <strong>
              {submissionResult.response.submission_outcome === "created"
                ? t("createdTitle")
                : t("replayedTitle")}
            </strong>
            <p>
              {submissionResult.response.submission_outcome === "created"
                ? t("createdDescription")
                : t("replayedDescription")}
            </p>
            <p>{t("returnedStatus")} <PaperJobStatusValue value={submissionResult.response.job.status} /></p>
            <p className="identity-line">{submissionResult.response.job.job_id}</p>
            <Link
              className="primary-link"
              href={`/paper-jobs/${encodeURIComponent(submissionResult.response.job.job_id)}`}
            >
              {t("inspectJob")}
            </Link>
            <RequestId value={submissionResult.requestId} />
          </div>
        ) : null}

        <fieldset className="form-section">
          <legend>{t("runIdentity")}</legend>
          <p className="form-section__description">{t("identityDescription")}</p>
          <div className="form-grid">
            <label>{t("runId")} <span className="required-label">{t("required")}</span><input id="run-id" aria-label={t("runId")} required placeholder="paper-run-20260118" value={runId} onChange={(event) => setRunId(event.target.value)} {...fieldA11y(errors, "run-id")} /><span className="field-guidance">{t("runGuidance")}</span><FieldError id="run-id-error" message={errors["run-id"]} /></label>
            <label>{t("createdTimestamp")} <span className="required-label">{t("required")}</span><input id="created-timestamp" aria-label={t("createdTimestamp")} required placeholder="2026-01-18T14:00:00Z" value={createdTimestamp} onChange={(event) => setCreatedTimestamp(event.target.value)} {...fieldA11y(errors, "created-timestamp")} /><span className="field-guidance">{t("timestampGuidance")}</span><FieldError id="created-timestamp-error" message={errors["created-timestamp"]} /></label>
            <label>{t("idempotencyKey")} <span className="optional-label">{t("optional")}</span><input id="idempotency-key" placeholder="founder-paper-run-v1" value={idempotencyKey} onChange={(event) => setIdempotencyKey(event.target.value)} aria-describedby="idempotency-guidance" /><span className="field-guidance" id="idempotency-guidance">{t("idempotencyGuidance")}</span></label>
          </div>
        </fieldset>

        <AccountSection legend={t("startingAccount")} prefix="starting" value={starting} setValue={setStarting} errors={errors} nextKey={nextKey} />
        <AccountSection legend={t("endingAccount")} prefix="ending" value={ending} setValue={setEnding} errors={errors} nextKey={nextKey} />

        <fieldset className="form-section">
          <legend>{t("orders")}</legend>
          <div className="repeatable-heading"><p className="form-section__description">{t("ordersDescription")}</p><button className="secondary-button" type="button" onClick={() => setOrders([...orders, { key: nextKey(), orderId: "", timestamp: "", symbol: "", side: "", quantity: "", status: "" }])}>{t("addOrder")}</button></div>
          {orders.length === 0 ? <p className="repeatable-empty">{t("noOrders")}</p> : <div className="repeatable-list">{orders.map((order, index) => <div className="repeatable-row" key={order.key}><span className="row-number">{t("orderNumber", { number: index + 1 })}</span>{([['orderId','orderId'],['timestamp','timestamp'],['symbol','symbol'],['side','side'],['quantity','quantity'],['status','status']] as const).map(([field,labelKey]) => { const name=`order-${index}-${field}`; const placeholder = field === "timestamp" ? "2026-01-18T14:01:00Z" : field === "symbol" ? "AAPL" : field === "quantity" ? "10" : field === "side" ? "buy" : field === "status" ? "filled" : "order-001"; return <label key={field}>{t(labelKey)} <span className="required-label">{t("required")}</span><input aria-label={t(labelKey)} required placeholder={placeholder} inputMode={field === 'quantity' ? 'decimal' : undefined} value={order[field]} onChange={(event) => setOrders(orders.map((row) => row.key === order.key ? { ...row, [field]: event.target.value } : row))} {...fieldA11y(errors,name)} /><FieldError id={`${name}-error`} message={errors[name]} /></label>; })}<button className="remove-button" type="button" onClick={() => setOrders(orders.filter((row) => row.key !== order.key))}>{t("removeOrder", { number: index + 1 })}</button></div>)}</div>}
        </fieldset>

        <fieldset className="form-section">
          <legend>{t("fills")}</legend>
          <div className="repeatable-heading"><p className="form-section__description">{t("fillsDescription")}</p><button className="secondary-button" type="button" onClick={() => setFills([...fills, { key: nextKey(), timestamp: "", symbol: "", side: "", quantity: "", price: "", orderId: "" }])}>{t("addFill")}</button></div>
          {fills.length === 0 ? <p className="repeatable-empty">{t("noFills")}</p> : <div className="repeatable-list">{fills.map((fill, index) => <div className="repeatable-row" key={fill.key}><span className="row-number">{t("fillNumber", { number: index + 1 })}</span>{([['timestamp','timestamp'],['symbol','symbol'],['side','side'],['quantity','quantity'],['price','price'],['orderId','orderId']] as const).map(([field,labelKey]) => { const name=`fill-${index}-${field}`; const optional = field === "orderId"; const placeholder = field === "timestamp" ? "2026-01-18T14:01:30Z" : field === "symbol" ? "AAPL" : field === "quantity" ? "10" : field === "price" ? "100.00" : field === "side" ? "buy" : "order-001"; return <label key={field}>{t(labelKey)} <span className={optional ? "optional-label" : "required-label"}>{optional ? t("optional") : t("required")}</span><input aria-label={t(labelKey)} required={!optional} placeholder={placeholder} inputMode={field === 'quantity' || field === 'price' ? 'decimal' : undefined} value={fill[field]} onChange={(event) => setFills(fills.map((row) => row.key === fill.key ? { ...row, [field]: event.target.value } : row))} {...fieldA11y(errors,name)} /><FieldError id={`${name}-error`} message={errors[name]} /></label>; })}<button className="remove-button" type="button" onClick={() => setFills(fills.filter((row) => row.key !== fill.key))}>{t("removeFill", { number: index + 1 })}</button></div>)}</div>}
        </fieldset>

        <div className="submission-actions"><button className="primary-button" type="submit" disabled={pending}>{pending ? t("submitting") : t("submit")}</button><p>{t("executionBoundary")}</p></div>
      </form>
    </div>
  );
}
