"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useRef, useState } from "react";

import { RequestId } from "@/components/data-states";
import {
  ApiClientError,
  submitPaperJob,
  type PaperJobSubmissionRequest,
} from "@/lib/api-client";
import { paperJobErrorTitle } from "@/lib/paper-jobs";

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
  const update = (field: keyof Omit<AccountInput, "positions">, next: string) =>
    setValue({ ...value, [field]: next });
  return (
    <fieldset className="form-section">
      <legend>{legend}</legend>
      <p className="form-section__description">Enter backend transport fields exactly; no account values are derived in the browser.</p>
      <div className="form-grid">
        {[
          ["timestamp", "Timestamp", value.timestamp],
          ["startingCash", "Starting cash", value.startingCash],
          ["currentCash", "Current cash", value.currentCash],
        ].map(([field, label, current]) => {
          const name = `${prefix}-${field}`;
          const numeric = field !== "timestamp";
          return (
            <label key={field}>
              {label}
              <input
                id={name}
                name={name}
                required
                inputMode={numeric ? "decimal" : undefined}
                value={current}
                onChange={(event) => update(field as "timestamp" | "startingCash" | "currentCash", event.target.value)}
                {...fieldA11y(errors, name)}
              />
              <FieldError id={`${name}-error`} message={errors[name]} />
            </label>
          );
        })}
      </div>
      <div className="repeatable-heading">
        <div><h3>Positions</h3><p>Optional exact symbol-to-quantity rows.</p></div>
        <button
          className="secondary-button"
          type="button"
          onClick={() => setValue({ ...value, positions: [...value.positions, { key: nextKey(), symbol: "", quantity: "" }] })}
        >
          Add position
        </button>
      </div>
      {value.positions.length === 0 ? <p className="repeatable-empty">No positions added.</p> : (
        <div className="repeatable-list">
          {value.positions.map((position, index) => {
            const symbolName = `${prefix}-position-${index}-symbol`;
            const quantityName = `${prefix}-position-${index}-quantity`;
            return (
              <div className="repeatable-row repeatable-row--position" key={position.key}>
                <span className="row-number">Position {index + 1}</span>
                <label>Symbol<input value={position.symbol} onChange={(event) => setValue({ ...value, positions: value.positions.map((row) => row.key === position.key ? { ...row, symbol: event.target.value } : row) })} {...fieldA11y(errors, symbolName)} /><FieldError id={`${symbolName}-error`} message={errors[symbolName]} /></label>
                <label>Quantity<input inputMode="decimal" value={position.quantity} onChange={(event) => setValue({ ...value, positions: value.positions.map((row) => row.key === position.key ? { ...row, quantity: event.target.value } : row) })} {...fieldA11y(errors, quantityName)} /><FieldError id={`${quantityName}-error`} message={errors[quantityName]} /></label>
                <button className="remove-button" type="button" onClick={() => setValue({ ...value, positions: value.positions.filter((row) => row.key !== position.key) })}>Remove position {index + 1}</button>
              </div>
            );
          })}
        </div>
      )}
    </fieldset>
  );
}

export function PaperJobSubmissionView() {
  const router = useRouter();
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
  const [serverError, setServerError] = useState<{ title: string; message: string; requestId: string | null } | null>(null);
  const nextKey = () => ++keyCounter.current;

  function buildRequest(): PaperJobSubmissionRequest | null {
    const nextErrors: FieldErrors = {};
    const required = (name: string, value: string): string => {
      if (value.length === 0) nextErrors[name] = "This transport field is required.";
      return value;
    };
    const numeric = (name: string, value: string): number => {
      if (value.length === 0) {
        nextErrors[name] = "Enter a finite number.";
        return 0;
      }
      const parsed = Number(value);
      if (!Number.isFinite(parsed)) nextErrors[name] = "Enter a finite number.";
      return parsed;
    };
    const account = (prefix: "starting" | "ending", input: AccountInput) => {
      const symbols = new Set<string>();
      let positionsValid = true;
      input.positions.forEach((position, index) => {
        const symbolName = `${prefix}-position-${index}-symbol`;
        const quantityName = `${prefix}-position-${index}-quantity`;
        if (position.symbol.length === 0) {
          nextErrors[symbolName] = "Position symbol is required.";
          positionsValid = false;
        } else if (symbols.has(position.symbol)) {
          nextErrors[symbolName] = "Duplicate position symbols are not allowed in one account state.";
          positionsValid = false;
        }
        symbols.add(position.symbol);
        numeric(quantityName, position.quantity);
        if (nextErrors[quantityName]) positionsValid = false;
      });
      const positions = positionsValid
        ? Object.fromEntries(input.positions.map((row, index) => [row.symbol, numeric(`${prefix}-position-${index}-quantity`, row.quantity)]))
        : {};
      return {
        timestamp: required(`${prefix}-timestamp`, input.timestamp),
        starting_cash: numeric(`${prefix}-startingCash`, input.startingCash),
        current_cash: numeric(`${prefix}-currentCash`, input.currentCash),
        positions,
      };
    };
    const request: PaperJobSubmissionRequest = {
      run_id: required("run-id", runId),
      created_timestamp: required("created-timestamp", createdTimestamp),
      starting_account_state: account("starting", starting),
      ending_account_state: account("ending", ending),
      orders: orders.map((order, index) => ({
        order_id: required(`order-${index}-orderId`, order.orderId),
        timestamp: required(`order-${index}-timestamp`, order.timestamp),
        symbol: required(`order-${index}-symbol`, order.symbol),
        side: required(`order-${index}-side`, order.side),
        quantity: numeric(`order-${index}-quantity`, order.quantity),
        status: required(`order-${index}-status`, order.status),
      })),
      fills: fills.map((fill, index) => ({
        timestamp: required(`fill-${index}-timestamp`, fill.timestamp),
        symbol: required(`fill-${index}-symbol`, fill.symbol),
        side: required(`fill-${index}-side`, fill.side),
        quantity: numeric(`fill-${index}-quantity`, fill.quantity),
        price: numeric(`fill-${index}-price`, fill.price),
        order_id: fill.orderId.length === 0 ? null : fill.orderId,
      })),
    };
    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0 ? request : null;
  }

  return (
    <div className="business-workspace">
      <div className="back-links"><Link className="text-link" href="/paper-jobs">← Back to paper jobs</Link></div>
      <header className="page-heading page-heading--detail">
        <p className="eyebrow">Paper runs · Explicit submission</p>
        <h1>Submit a queued job</h1>
        <p>Submission creates or exactly replays durable queued state. It never runs the job; Run remains a separate confirmed action on the detail page.</p>
      </header>

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
        void submitPaperJob(request, idempotencyKey).then((result) => {
          router.push(`/paper-jobs/${encodeURIComponent(result.data.job_id)}`);
        }).catch((error: unknown) => {
          if (error instanceof ApiClientError) {
            setServerError({ title: paperJobErrorTitle(error.code), message: error.publicMessage, requestId: error.requestId });
          } else {
            setServerError({ title: "Paper job operation failed", message: "The local API is unavailable.", requestId: null });
          }
        }).finally(() => {
          pendingRef.current = false;
          setPending(false);
        });
      }}>
        {Object.keys(errors).length > 0 ? <div className="form-alert" role="alert"><strong>Submission fields need attention.</strong><span>Correct the associated required or numeric fields before sending.</span></div> : null}
        {serverError ? <div className="form-alert form-alert--server" role="alert"><strong>{serverError.title}</strong><span>{serverError.message}</span><RequestId value={serverError.requestId} /></div> : null}

        <fieldset className="form-section">
          <legend>Job identity</legend>
          <p className="form-section__description">Values are sent exactly as entered. A nonblank idempotency key is optional.</p>
          <div className="form-grid">
            <label>Run ID<input id="run-id" value={runId} onChange={(event) => setRunId(event.target.value)} {...fieldA11y(errors, "run-id")} /><FieldError id="run-id-error" message={errors["run-id"]} /></label>
            <label>Created timestamp<input id="created-timestamp" value={createdTimestamp} onChange={(event) => setCreatedTimestamp(event.target.value)} {...fieldA11y(errors, "created-timestamp")} /><FieldError id="created-timestamp-error" message={errors["created-timestamp"]} /></label>
            <label>Idempotency key <span className="optional-label">Optional</span><input id="idempotency-key" value={idempotencyKey} onChange={(event) => setIdempotencyKey(event.target.value)} aria-describedby="idempotency-guidance" /><span className="field-guidance" id="idempotency-guidance">Sent only when nonblank; exact replay and conflicts remain backend-owned.</span></label>
          </div>
        </fieldset>

        <AccountSection legend="Starting account state" prefix="starting" value={starting} setValue={setStarting} errors={errors} nextKey={nextKey} />
        <AccountSection legend="Ending account state" prefix="ending" value={ending} setValue={setEnding} errors={errors} nextKey={nextKey} />

        <fieldset className="form-section">
          <legend>Orders</legend>
          <div className="repeatable-heading"><p className="form-section__description">Rows are sent in the exact order shown.</p><button className="secondary-button" type="button" onClick={() => setOrders([...orders, { key: nextKey(), orderId: "", timestamp: "", symbol: "", side: "", quantity: "", status: "" }])}>Add order</button></div>
          {orders.length === 0 ? <p className="repeatable-empty">No orders added.</p> : <div className="repeatable-list">{orders.map((order, index) => <div className="repeatable-row" key={order.key}><span className="row-number">Order {index + 1}</span>{([['orderId','Order ID'],['timestamp','Timestamp'],['symbol','Symbol'],['side','Side'],['quantity','Quantity'],['status','Status']] as const).map(([field,label]) => { const name=`order-${index}-${field}`; return <label key={field}>{label}<input inputMode={field === 'quantity' ? 'decimal' : undefined} value={order[field]} onChange={(event) => setOrders(orders.map((row) => row.key === order.key ? { ...row, [field]: event.target.value } : row))} {...fieldA11y(errors,name)} /><FieldError id={`${name}-error`} message={errors[name]} /></label>; })}<button className="remove-button" type="button" onClick={() => setOrders(orders.filter((row) => row.key !== order.key))}>Remove order {index + 1}</button></div>)}</div>}
        </fieldset>

        <fieldset className="form-section">
          <legend>Fills</legend>
          <div className="repeatable-heading"><p className="form-section__description">Blank optional order ID is sent as null. Row order is preserved.</p><button className="secondary-button" type="button" onClick={() => setFills([...fills, { key: nextKey(), timestamp: "", symbol: "", side: "", quantity: "", price: "", orderId: "" }])}>Add fill</button></div>
          {fills.length === 0 ? <p className="repeatable-empty">No fills added.</p> : <div className="repeatable-list">{fills.map((fill, index) => <div className="repeatable-row" key={fill.key}><span className="row-number">Fill {index + 1}</span>{([['timestamp','Timestamp'],['symbol','Symbol'],['side','Side'],['quantity','Quantity'],['price','Price'],['orderId','Order ID (optional)']] as const).map(([field,label]) => { const name=`fill-${index}-${field}`; return <label key={field}>{label}<input inputMode={field === 'quantity' || field === 'price' ? 'decimal' : undefined} value={fill[field]} onChange={(event) => setFills(fills.map((row) => row.key === fill.key ? { ...row, [field]: event.target.value } : row))} {...fieldA11y(errors,name)} /><FieldError id={`${name}-error`} message={errors[name]} /></label>; })}<button className="remove-button" type="button" onClick={() => setFills(fills.filter((row) => row.key !== fill.key))}>Remove fill {index + 1}</button></div>)}</div>}
        </fieldset>

        <div className="submission-actions"><button className="primary-button" type="submit" disabled={pending}>{pending ? "Submitting queued job…" : "Submit queued job"}</button><p>Execution will not start from this form.</p></div>
      </form>
    </div>
  );
}
