"use client";

import { useTranslations } from "next-intl";
import { useCallback, useMemo, useState } from "react";

import { ErrorState, LoadingState } from "@/components/data-states";
import {
  ApiClientError,
  createOrderIntent,
  createPreTradeRiskDecision,
  evaluateStrategySignal,
  fetchMarketDataReplayDetail,
  fetchMarketDataReplays,
  fetchPaperAccountDetail,
  fetchPaperAccounts,
  fetchTradingCalendarDetail,
  fetchTradingCalendars,
  type MarketDataReplayDetailResponse,
  type OrderIntentCommandResponse,
  type OrderIntentCreateRequest,
  type PaperAccountDetailResponse,
  type PreTradeRiskDecisionCommandResponse,
  type PreTradeRiskDecisionCreateRequest,
  type StrategySignalCommandResponse,
  type StrategySignalEvaluateRequest,
  type TradingCalendarDetailResponse,
} from "@/lib/api-client";
import { useApiResource } from "@/lib/use-api-resource";

type CommandError = Readonly<{
  code: string;
  message: string;
  requestId: string | null;
  httpStatus: number | null;
}>;

type ManualResource<Data> =
  | Readonly<{ status: "idle" }>
  | Readonly<{ status: "loading" }>
  | Readonly<{ status: "success"; data: Data; requestId: string | null }>
  | Readonly<{ status: "error"; error: CommandError }>;

type CommandStatus = "idle" | "pending" | "settled";

type SignalEvidence = Readonly<{
  response: StrategySignalCommandResponse;
  draftFingerprint: string;
}>;

type IntentEvidence = Readonly<{
  response: OrderIntentCommandResponse;
  draftFingerprint: string;
}>;

type RiskEvidence = Readonly<{
  response: PreTradeRiskDecisionCommandResponse;
  draftFingerprint: string;
}>;

type StepKeyState = Readonly<{
  fingerprint: string;
  key: string;
}>;

type StepName = "signal" | "intent" | "risk";

function commandError(error: unknown): CommandError {
  if (error instanceof ApiClientError) {
    return {
      code: error.code,
      message: error.publicMessage,
      requestId: error.requestId,
      httpStatus: error.status > 0 ? error.status : null,
    };
  }
  return {
    code: "api_unavailable",
    message: "The local API is unavailable.",
    requestId: null,
    httpStatus: null,
  };
}

function positiveInteger(value: string): number | null {
  if (!/^[1-9][0-9]*$/.test(value)) return null;
  const parsed = Number(value);
  return Number.isSafeInteger(parsed) ? parsed : null;
}

function fingerprint(value: object): string {
  return JSON.stringify(value);
}

function freshKey(step: StepName): string {
  return `s204-${step}-${globalThis.crypto.randomUUID()}`;
}

function keyForDraft(
  step: StepName,
  draftFingerprint: string,
  current: StepKeyState | null,
): StepKeyState {
  return current?.fingerprint === draftFingerprint
    ? current
    : { fingerprint: draftFingerprint, key: freshKey(step) };
}

function RawValue({ value }: { value: string | number | boolean | null }) {
  return <code className="raw-value">{value === null ? "null" : String(value)}</code>;
}

function Definition({
  label,
  value,
}: {
  label: string;
  value: string | number | boolean | null;
}) {
  return (
    <div>
      <dt>{label}</dt>
      <dd><RawValue value={value} /></dd>
    </div>
  );
}

function StepError({
  error,
  operation,
  title,
  retryLabel,
  onRetry,
}: {
  error: CommandError;
  operation: string;
  title: string;
  retryLabel: string;
  onRetry: () => void;
}) {
  return (
    <ErrorState
      code={error.code}
      title={title}
      message={error.message}
      requestId={error.requestId}
      httpStatus={error.httpStatus}
      operation={operation}
      retryLabel={retryLabel}
      onRetry={onRetry}
    />
  );
}

function SignalInspection({ evidence }: { evidence: SignalEvidence }) {
  const t = useTranslations("strategyToRisk.signal");
  const signal = evidence.response.signal;
  const runtime = signal.strategy_runtime_reference;
  const market = signal.market_reference;
  return (
    <section className="immutable-evidence" aria-labelledby="signal-evidence-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">{t("evidenceEyebrow")}</p>
          <h3 id="signal-evidence-title">{t("evidenceTitle")}</h3>
        </div>
        <p>{evidence.response.replayed ? t("replayed") : t("created")}</p>
      </div>
      <dl className="definition-grid definition-grid--wide">
        <Definition label={t("requestId")} value={evidence.response.request_id} />
        <Definition label={t("replayedRaw")} value={evidence.response.replayed} />
        <Definition label={t("signalId")} value={signal.signal_id} />
        <Definition label={t("signalDigest")} value={signal.signal_digest} />
        <Definition label={t("strategyName")} value={runtime.strategy_name} />
        <Definition label={t("strategyVersion")} value={runtime.strategy_version} />
        <Definition label={t("adapterVersion")} value={runtime.adapter_version} />
        <Definition label={t("runtimeSemantics")} value={runtime.runtime_sizing_semantics} />
        <Definition label={t("fastWindow")} value={runtime.parameters.fast_window} />
        <Definition label={t("slowWindow")} value={runtime.parameters.slow_window} />
        <Definition label={t("parametersDigest")} value={runtime.parameters_digest} />
        <Definition label={t("runtimeDigest")} value={runtime.reference_digest} />
        <Definition label={t("calendarId")} value={market.calendar_id} />
        <Definition label={t("calendarVersion")} value={market.calendar_version} />
        <Definition label={t("sessionId")} value={market.trading_session_id} />
        <Definition label={t("replayId")} value={market.replay_id} />
        <Definition label={t("streamDigest")} value={market.event_stream_digest} />
        <Definition label={t("cursorPosition")} value={market.cursor_position} />
        <Definition label={t("lastEventId")} value={market.last_event_id} />
        <Definition label={t("signalEventId")} value={market.signal_event_id} />
        <Definition label={t("signalTime")} value={market.signal_time} />
        <Definition label={t("instrumentId")} value={market.instrument_id} />
        <Definition label={t("marketDigest")} value={market.reference_digest} />
        <Definition label={t("targetSemantics")} value={signal.target_semantics} />
        <Definition label={t("targetQuantity")} value={signal.target_position_quantity} />
        <Definition label={t("createdAt")} value={signal.created_at} />
      </dl>
    </section>
  );
}

function IntentInspection({ evidence }: { evidence: IntentEvidence }) {
  const t = useTranslations("strategyToRisk.intent");
  const result = evidence.response.result;
  const isIntent = evidence.response.result_kind === "order_intent";
  const account = result.account_reference;
  const market = result.market_reference;
  return (
    <section className="immutable-evidence" aria-labelledby="intent-evidence-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">{t("evidenceEyebrow")}</p>
          <h3 id="intent-evidence-title">
            {isIntent ? t("intentEvidenceTitle") : t("noActionEvidenceTitle")}
          </h3>
        </div>
        <p>{evidence.response.replayed ? t("replayed") : t("created")}</p>
      </div>
      <dl className="definition-grid definition-grid--wide">
        <Definition label={t("requestId")} value={evidence.response.request_id} />
        <Definition label={t("resultKind")} value={evidence.response.result_kind} />
        <Definition label={t("replayedRaw")} value={evidence.response.replayed} />
        {evidence.response.result_kind === "order_intent" ? (
          <>
            <Definition label={t("intentId")} value={evidence.response.result.intent_id} />
            <Definition label={t("intentDigest")} value={evidence.response.result.intent_digest} />
            <Definition label={t("side")} value={evidence.response.result.side} />
            <Definition label={t("requestedQuantity")} value={evidence.response.result.requested_quantity} />
          </>
        ) : (
          <>
            <Definition label={t("noActionId")} value={evidence.response.result.no_action_id} />
            <Definition label={t("noActionDigest")} value={evidence.response.result.no_action_digest} />
            <Definition label={t("reasonCode")} value={evidence.response.result.reason_code} />
          </>
        )}
        <Definition label={t("signalId")} value={result.signal_reference.signal_id} />
        <Definition label={t("signalDigest")} value={result.signal_reference.signal_digest} />
        <Definition label={t("calendarId")} value={market.calendar_id} />
        <Definition label={t("calendarVersion")} value={market.calendar_version} />
        <Definition label={t("sessionId")} value={market.trading_session_id} />
        <Definition label={t("replayId")} value={market.replay_id} />
        <Definition label={t("streamDigest")} value={market.event_stream_digest} />
        <Definition label={t("cursorPosition")} value={market.cursor_position} />
        <Definition label={t("signalEventId")} value={market.signal_event_id} />
        <Definition label={t("signalTime")} value={market.signal_time} />
        <Definition label={t("instrumentId")} value={market.instrument_id} />
        <Definition label={t("marketDigest")} value={market.reference_digest} />
        <Definition label={t("accountId")} value={account.account_id} />
        <Definition label={t("accountStatus")} value={account.lifecycle_status} />
        <Definition label={t("accountVersion")} value={account.account_head_version} />
        <Definition label={t("accountEventId")} value={account.account_head_event_id} />
        <Definition label={t("accountChainDigest")} value={account.account_head_chain_digest} />
        <Definition label={t("accountReferenceDigest")} value={account.reference_digest} />
        <Definition label={t("baseCurrency")} value={account.base_currency} />
        <Definition label={t("cashBalance")} value={account.cash_balance} />
        <Definition label={t("availableCash")} value={account.available_cash} />
        <Definition label={t("targetSemantics")} value={result.target_semantics} />
        <Definition label={t("targetQuantity")} value={result.target_position_quantity} />
        <Definition label={t("currentQuantity")} value={result.current_position_quantity} />
        <Definition label={t("policyVersion")} value={result.intent_policy_version} />
        <Definition label={t("originDigest")} value={result.origin_command_digest} />
        <Definition label={t("originActor")} value={result.origin_actor} />
        <Definition label={t("createdAt")} value={result.created_at} />
      </dl>
      {!isIntent ? <p className="neutral-note" role="status">{t("noActionTerminal")}</p> : null}
    </section>
  );
}

function RiskInspection({ evidence }: { evidence: RiskEvidence }) {
  const t = useTranslations("strategyToRisk.risk");
  const decision = evidence.response.decision;
  const snapshot = decision.input_snapshot;
  const account = snapshot.account_reference;
  const market = snapshot.market_reference;
  const policy = snapshot.risk_policy_reference;
  const price = snapshot.price_reference;
  return (
    <section className="immutable-evidence" aria-labelledby="risk-evidence-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">{t("evidenceEyebrow")}</p>
          <h3 id="risk-evidence-title">{t("evidenceTitle")}</h3>
        </div>
        <p>
          {evidence.response.replayed ? t("replayed") : t("created")} · {decision.outcome === "allow" ? t("allowNotice") : t("rejectNotice")}
        </p>
      </div>
      <dl className="definition-grid definition-grid--wide">
        <Definition label={t("requestId")} value={evidence.response.request_id} />
        <Definition label={t("replayedRaw")} value={evidence.response.replayed} />
        <Definition label={t("decisionId")} value={decision.decision_id} />
        <Definition label={t("decisionDigest")} value={decision.decision_digest} />
        <Definition label={t("outcome")} value={decision.outcome} />
        <Definition label={t("reasonCodes")} value={decision.reason_codes.length === 0 ? "[]" : decision.reason_codes.join(",")} />
        <Definition label={t("snapshotId")} value={snapshot.snapshot_id} />
        <Definition label={t("snapshotDigest")} value={snapshot.snapshot_digest} />
        <Definition label={t("intentId")} value={snapshot.intent_reference.intent_id} />
        <Definition label={t("intentDigest")} value={snapshot.intent_reference.intent_digest} />
        <Definition label={t("side")} value={snapshot.side} />
        <Definition label={t("requestedQuantity")} value={snapshot.requested_quantity} />
        <Definition label={t("availableCash")} value={snapshot.verified_available_cash} />
        <Definition label={t("currentQuantity")} value={snapshot.verified_current_instrument_quantity} />
        <Definition label={t("estimatedNotional")} value={snapshot.estimated_order_notional} />
        <Definition label={t("accountId")} value={account.account_id} />
        <Definition label={t("accountStatus")} value={account.lifecycle_status} />
        <Definition label={t("accountVersion")} value={account.account_head_version} />
        <Definition label={t("accountEventId")} value={account.account_head_event_id} />
        <Definition label={t("accountChainDigest")} value={account.account_head_chain_digest} />
        <Definition label={t("accountReferenceDigest")} value={account.reference_digest} />
        <Definition label={t("baseCurrency")} value={account.base_currency} />
        <Definition label={t("cashBalance")} value={account.cash_balance} />
        <Definition label={t("accountInstrumentId")} value={account.instrument_id} />
        <Definition label={t("calendarId")} value={market.calendar_id} />
        <Definition label={t("calendarVersion")} value={market.calendar_version} />
        <Definition label={t("sessionId")} value={market.trading_session_id} />
        <Definition label={t("replayId")} value={market.replay_id} />
        <Definition label={t("streamDigest")} value={market.event_stream_digest} />
        <Definition label={t("cursorPosition")} value={market.cursor_position} />
        <Definition label={t("currentEventId")} value={market.signal_event_id} />
        <Definition label={t("lastEventId")} value={market.last_event_id} />
        <Definition label={t("currentEventTime")} value={market.signal_time} />
        <Definition label={t("instrumentId")} value={market.instrument_id} />
        <Definition label={t("marketDigest")} value={market.reference_digest} />
        <Definition label={t("policyId")} value={policy.policy_id} />
        <Definition label={t("pricePolicyId")} value={policy.reference_price_policy_id} />
        <Definition label={t("maximumQuantity")} value={policy.maximum_order_quantity} />
        <Definition label={t("maximumNotional")} value={policy.maximum_order_notional} />
        <Definition label={t("policyDigest")} value={policy.configuration_digest} />
        <Definition label={t("policyReferenceDigest")} value={policy.reference_digest} />
        <Definition label={t("referencePrice")} value={price.reference_price} />
        <Definition label={t("priceReplayId")} value={price.replay_id} />
        <Definition label={t("priceStreamDigest")} value={price.event_stream_digest} />
        <Definition label={t("priceCursorPosition")} value={price.cursor_position} />
        <Definition label={t("priceInstrumentId")} value={price.instrument_id} />
        <Definition label={t("priceEventId")} value={price.price_event_id} />
        <Definition label={t("priceEventPosition")} value={price.price_event_position} />
        <Definition label={t("priceEventTime")} value={price.price_event_time} />
        <Definition label={t("priceEventDigest")} value={price.price_event_digest} />
        <Definition label={t("priceReferenceDigest")} value={price.reference_digest} />
        <Definition label={t("originDigest")} value={decision.origin_command_digest} />
        <Definition label={t("originActor")} value={decision.origin_actor} />
        <Definition label={t("createdAt")} value={decision.created_at} />
      </dl>
      <section className="subsection" aria-labelledby="risk-rules-title">
        <h4 id="risk-rules-title">{t("rulesTitle")}</h4>
        <ol className="strategy-risk-rules">
          {snapshot.rule_evidence.map((rule) => (
            <li key={rule.rule_code}>
              <dl className="definition-grid definition-grid--wide">
                <Definition label={t("ruleCode")} value={rule.rule_code} />
                <Definition label={t("applicable")} value={rule.applicable} />
                <Definition label={t("passed")} value={rule.passed} />
                <Definition label={t("valueType")} value={rule.value_type} />
                <Definition label={t("observedValue")} value={rule.observed_value} />
                <Definition label={t("thresholdValue")} value={rule.threshold_value} />
                <Definition label={t("ruleDigest")} value={rule.rule_digest} />
              </dl>
            </li>
          ))}
        </ol>
      </section>
      <p className="boundary-note strategy-risk-decision-note">
        {decision.outcome === "allow" ? t("allowBoundary") : t("rejectBoundary")}
      </p>
    </section>
  );
}

export function StrategyToRiskWorkspace() {
  const t = useTranslations("strategyToRisk");
  const common = useTranslations("common");

  const [actor, setActor] = useState("founder");
  const [fastWindow, setFastWindow] = useState("20");
  const [slowWindow, setSlowWindow] = useState("50");
  const [targetQuantity, setTargetQuantity] = useState("100");
  const [accountId, setAccountId] = useState("");
  const [calendarId, setCalendarId] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [replayId, setReplayId] = useState("");
  const [instrumentId, setInstrumentId] = useState("");
  const [maximumQuantity, setMaximumQuantity] = useState("");
  const [maximumNotional, setMaximumNotional] = useState("");

  const [accountDetail, setAccountDetail] =
    useState<ManualResource<PaperAccountDetailResponse>>({ status: "idle" });
  const [calendarDetail, setCalendarDetail] =
    useState<ManualResource<TradingCalendarDetailResponse>>({ status: "idle" });
  const [replayDetail, setReplayDetail] =
    useState<ManualResource<MarketDataReplayDetailResponse>>({ status: "idle" });

  const [signalStatus, setSignalStatus] = useState<CommandStatus>("idle");
  const [intentStatus, setIntentStatus] = useState<CommandStatus>("idle");
  const [riskStatus, setRiskStatus] = useState<CommandStatus>("idle");
  const [signalError, setSignalError] = useState<CommandError | null>(null);
  const [intentError, setIntentError] = useState<CommandError | null>(null);
  const [riskError, setRiskError] = useState<CommandError | null>(null);
  const [signalEvidence, setSignalEvidence] = useState<SignalEvidence | null>(null);
  const [intentEvidence, setIntentEvidence] = useState<IntentEvidence | null>(null);
  const [riskEvidence, setRiskEvidence] = useState<RiskEvidence | null>(null);
  const [signalKey, setSignalKey] = useState<StepKeyState | null>(null);
  const [intentKey, setIntentKey] = useState<StepKeyState | null>(null);
  const [riskKey, setRiskKey] = useState<StepKeyState | null>(null);

  const loadOptions = useCallback(async () => {
    const [accounts, calendars, replays] = await Promise.all([
      fetchPaperAccounts({ lifecycleStatus: null, limit: 200, cursor: null }),
      fetchTradingCalendars(),
      fetchMarketDataReplays(),
    ]);
    return {
      data: {
        accounts: accounts.data,
        calendars: calendars.data,
        replays: replays.data,
      },
      requestId: accounts.requestId ?? calendars.requestId ?? replays.requestId,
    };
  }, []);
  const options = useApiResource(loadOptions);

  const selectedAccount =
    accountDetail.status === "success" &&
    accountDetail.data.account.account_id === accountId
      ? accountDetail.data
      : null;
  const selectedCalendar =
    calendarDetail.status === "success" &&
    calendarDetail.data.calendar.id === calendarId
      ? calendarDetail.data
      : null;
  const selectedReplay =
    replayDetail.status === "success" &&
    replayDetail.data.session.replay_id === replayId
      ? replayDetail.data
      : null;
  const selectedSession = selectedCalendar?.sessions.find(
    (session) => session.id === sessionId,
  ) ?? null;

  const signalRequest = useMemo<StrategySignalEvaluateRequest | null>(() => {
    const fast = positiveInteger(fastWindow);
    const slow = positiveInteger(slowWindow);
    const cursor = selectedReplay?.session.cursor;
    if (
      fast === null ||
      slow === null ||
      actor.length === 0 ||
      actor !== actor.trim() ||
      targetQuantity.length === 0 ||
      instrumentId.length === 0 ||
      instrumentId !== instrumentId.trim() ||
      selectedCalendar === null ||
      selectedSession === null ||
      selectedReplay === null ||
      cursor === undefined ||
      cursor.position <= 0 ||
      cursor.last_event_id === null
    ) {
      return null;
    }
    return {
      runtime: {
        strategy_name: "moving_average_crossover",
        strategy_version: "v1",
        adapter_version: "v1",
        runtime_sizing_semantics: "target_position_quantity",
        fast_window: fast,
        slow_window: slow,
        target_position_quantity: targetQuantity,
      },
      market: {
        calendar_id: selectedCalendar.calendar.id,
        expected_calendar_version: selectedCalendar.calendar.calendar_version,
        trading_session_id: selectedSession.id,
        replay_id: selectedReplay.session.replay_id,
        expected_event_stream_digest: cursor.event_stream_digest,
        expected_cursor_position: cursor.position,
        expected_signal_event_id: cursor.last_event_id,
        expected_signal_time_utc: cursor.current_event_time,
        instrument_id: instrumentId,
      },
      actor,
    };
  }, [
    actor,
    fastWindow,
    instrumentId,
    selectedCalendar,
    selectedReplay,
    selectedSession,
    slowWindow,
    targetQuantity,
  ]);
  const signalFingerprint = signalRequest === null ? null : fingerprint(signalRequest);
  const signalAligned =
    signalEvidence !== null &&
    signalFingerprint !== null &&
    signalEvidence.draftFingerprint === signalFingerprint;

  const intentRequest = useMemo<OrderIntentCreateRequest | null>(() => {
    if (
      !signalAligned ||
      signalEvidence === null ||
      selectedAccount === null ||
      selectedAccount.account.lifecycle_status !== "active"
    ) {
      return null;
    }
    return {
      signal_id: signalEvidence.response.signal.signal_id,
      account: {
        account_id: selectedAccount.account.account_id,
        expected_account_head_version: selectedAccount.account.head_version,
        expected_account_head_event_id: selectedAccount.account.head_event_id,
        expected_account_head_chain_digest: selectedAccount.account.head_chain_digest,
      },
      intent_policy_version: "target_position_quantity_delta_v1",
      actor,
    };
  }, [actor, selectedAccount, signalAligned, signalEvidence]);
  const intentFingerprint = intentRequest === null ? null : fingerprint(intentRequest);
  const intentAligned =
    intentEvidence !== null &&
    intentFingerprint !== null &&
    intentEvidence.draftFingerprint === intentFingerprint;

  const riskRequest = useMemo<PreTradeRiskDecisionCreateRequest | null>(() => {
    const cursor = selectedReplay?.session.cursor;
    if (
      !intentAligned ||
      intentEvidence === null ||
      intentEvidence.response.result_kind !== "order_intent" ||
      selectedAccount === null ||
      selectedCalendar === null ||
      selectedSession === null ||
      selectedReplay === null ||
      cursor === undefined ||
      cursor.position <= 0 ||
      cursor.last_event_id === null
    ) {
      return null;
    }
    return {
      intent_id: intentEvidence.response.result.intent_id,
      policy: {
        policy_id: "long_only_cash_risk_v1",
        reference_price_policy_id: "latest_trade_price_v1",
        maximum_order_quantity: maximumQuantity.length === 0 ? null : maximumQuantity,
        maximum_order_notional: maximumNotional.length === 0 ? null : maximumNotional,
      },
      account: {
        expected_account_head_version: selectedAccount.account.head_version,
        expected_account_head_event_id: selectedAccount.account.head_event_id,
        expected_account_head_chain_digest: selectedAccount.account.head_chain_digest,
      },
      market: {
        expected_calendar_id: selectedCalendar.calendar.id,
        expected_calendar_version: selectedCalendar.calendar.calendar_version,
        expected_trading_session_id: selectedSession.id,
        expected_replay_id: selectedReplay.session.replay_id,
        expected_event_stream_digest: cursor.event_stream_digest,
        expected_cursor_position: cursor.position,
        expected_current_event_id: cursor.last_event_id,
        expected_current_event_time_utc: cursor.current_event_time,
        expected_instrument_id: instrumentId,
      },
      actor,
    };
  }, [
    actor,
    instrumentId,
    intentAligned,
    intentEvidence,
    maximumNotional,
    maximumQuantity,
    selectedAccount,
    selectedCalendar,
    selectedReplay,
    selectedSession,
  ]);
  const riskFingerprint = riskRequest === null ? null : fingerprint(riskRequest);
  const riskAligned =
    riskEvidence !== null &&
    riskFingerprint !== null &&
    riskEvidence.draftFingerprint === riskFingerprint;

  async function loadAccount() {
    if (accountId.length === 0) return;
    setAccountDetail({ status: "loading" });
    try {
      const result = await fetchPaperAccountDetail(accountId);
      setAccountDetail({ status: "success", data: result.data, requestId: result.requestId });
    } catch (error: unknown) {
      setAccountDetail({ status: "error", error: commandError(error) });
    }
  }

  async function loadCalendar() {
    if (calendarId.length === 0) return;
    setCalendarDetail({ status: "loading" });
    try {
      const result = await fetchTradingCalendarDetail(calendarId);
      setCalendarDetail({ status: "success", data: result.data, requestId: result.requestId });
      setSessionId("");
    } catch (error: unknown) {
      setCalendarDetail({ status: "error", error: commandError(error) });
    }
  }

  async function loadReplay() {
    if (replayId.length === 0) return;
    setReplayDetail({ status: "loading" });
    try {
      const result = await fetchMarketDataReplayDetail(replayId);
      setReplayDetail({ status: "success", data: result.data, requestId: result.requestId });
    } catch (error: unknown) {
      setReplayDetail({ status: "error", error: commandError(error) });
    }
  }

  async function submitSignal() {
    if (signalRequest === null || signalFingerprint === null || signalStatus === "pending") return;
    const keyState = keyForDraft("signal", signalFingerprint, signalKey);
    setSignalKey(keyState);
    setSignalStatus("pending");
    setSignalError(null);
    try {
      const result = await evaluateStrategySignal(signalRequest, keyState.key);
      setSignalEvidence({ response: result.data, draftFingerprint: signalFingerprint });
      setSignalStatus("settled");
    } catch (error: unknown) {
      setSignalError(commandError(error));
      setSignalStatus("settled");
    }
  }

  async function submitIntent() {
    if (intentRequest === null || intentFingerprint === null || intentStatus === "pending") return;
    const keyState = keyForDraft("intent", intentFingerprint, intentKey);
    setIntentKey(keyState);
    setIntentStatus("pending");
    setIntentError(null);
    try {
      const result = await createOrderIntent(intentRequest, keyState.key);
      setIntentEvidence({ response: result.data, draftFingerprint: intentFingerprint });
      setIntentStatus("settled");
    } catch (error: unknown) {
      setIntentError(commandError(error));
      setIntentStatus("settled");
    }
  }

  async function submitRisk() {
    if (riskRequest === null || riskFingerprint === null || riskStatus === "pending") return;
    const keyState = keyForDraft("risk", riskFingerprint, riskKey);
    setRiskKey(keyState);
    setRiskStatus("pending");
    setRiskError(null);
    try {
      const result = await createPreTradeRiskDecision(riskRequest, keyState.key);
      setRiskEvidence({ response: result.data, draftFingerprint: riskFingerprint });
      setRiskStatus("settled");
    } catch (error: unknown) {
      setRiskError(commandError(error));
      setRiskStatus("settled");
    }
  }

  return (
    <div className="business-workspace strategy-risk-workflow">
      <header className="page-heading">
        <p className="eyebrow">{t("eyebrow")}</p>
        <h1>{t("title")}</h1>
        <p>{t("description")}</p>
      </header>

      <aside className="boundary-note" aria-label={t("authorityTitle")}>
        <strong>{t("authorityTitle")}</strong>
        <p>{t("authority")}</p>
      </aside>

      <section className="content-panel" aria-labelledby="authority-selection-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow">{t("selection.eyebrow")}</p>
            <h2 id="authority-selection-title">{t("selection.title")}</h2>
          </div>
          <p>{t("selection.description")}</p>
        </div>

        {options.state.status === "loading" ? (
          <LoadingState message={t("selection.loading")} />
        ) : options.state.status === "error" ? (
          <ErrorState
            code={options.state.code}
            title={t("selection.unavailable")}
            message={options.state.message}
            requestId={options.state.requestId}
            httpStatus={options.state.httpStatus}
            operation="strategy_to_risk.selection.list"
            onRetry={options.retry}
          />
        ) : (
          <div className="strategy-risk-selection-grid">
            <fieldset className="form-section">
              <legend>{t("selection.runtimeTitle")}</legend>
              <p className="form-section__description">{t("selection.runtimeDescription")}</p>
              <div className="form-grid">
                <label>{t("selection.strategyName")}<input value="moving_average_crossover" readOnly /></label>
                <label>{t("selection.strategyVersion")}<input value="v1" readOnly /></label>
                <label>{t("selection.adapterVersion")}<input value="v1" readOnly /></label>
                <label className="form-grid__wide">{t("selection.sizingSemantics")}<input value="target_position_quantity" readOnly /></label>
                <label>{t("selection.fastWindow")}<input inputMode="numeric" value={fastWindow} onChange={(event) => setFastWindow(event.target.value)} /></label>
                <label>{t("selection.slowWindow")}<input inputMode="numeric" value={slowWindow} onChange={(event) => setSlowWindow(event.target.value)} /></label>
                <label>{t("selection.targetQuantity")}<input value={targetQuantity} onChange={(event) => setTargetQuantity(event.target.value)} /></label>
                <label className="form-grid__wide">{t("selection.actor")}<input value={actor} onChange={(event) => setActor(event.target.value)} /></label>
              </div>
            </fieldset>

            <fieldset className="form-section">
              <legend>{t("selection.accountTitle")}</legend>
              <p className="form-section__description">{t("selection.accountDescription")}</p>
              <label>
                {t("selection.account")}
                <select value={accountId} onChange={(event) => setAccountId(event.target.value)}>
                  <option value="">{t("selection.chooseAccount")}</option>
                  {options.state.data.accounts.items.map((account) => (
                    <option key={account.account_id} value={account.account_id}>
                      {account.display_name} | {account.account_id} | {account.lifecycle_status}
                    </option>
                  ))}
                </select>
              </label>
              <div className="submission-actions">
                <button className="secondary-button" type="button" disabled={accountId.length === 0 || accountDetail.status === "loading"} onClick={() => void loadAccount()}>
                  {accountDetail.status === "loading" ? t("selection.loadingAccount") : t("selection.loadAccount")}
                </button>
              </div>
              {accountDetail.status === "error" ? (
                <StepError error={accountDetail.error} operation="paper_account.detail" title={t("selection.accountUnavailable")} retryLabel={t("selection.retryLoad")} onRetry={() => void loadAccount()} />
              ) : null}
              {selectedAccount ? (
                <dl className="definition-grid definition-grid--wide">
                  <Definition label={t("selection.accountId")} value={selectedAccount.account.account_id} />
                  <Definition label={t("selection.lifecycleStatus")} value={selectedAccount.account.lifecycle_status} />
                  <Definition label={t("selection.headVersion")} value={selectedAccount.account.head_version} />
                  <Definition label={t("selection.headEventId")} value={selectedAccount.account.head_event_id} />
                  <Definition label={t("selection.headChainDigest")} value={selectedAccount.account.head_chain_digest} />
                  <Definition label={t("selection.baseCurrency")} value={selectedAccount.account.base_currency} />
                  <Definition label={t("selection.projectionStatus")} value={selectedAccount.account.projection_status} />
                  <Definition label={t("selection.availableCash")} value={selectedAccount.projection.available_cash} />
                </dl>
              ) : null}
              {selectedAccount && selectedAccount.account.lifecycle_status !== "active" ? (
                <p className="form-error" role="alert">{t("selection.accountInactive")}</p>
              ) : null}
            </fieldset>

            <fieldset className="form-section">
              <legend>{t("selection.marketTitle")}</legend>
              <p className="form-section__description">{t("selection.marketDescription")}</p>
              <div className="form-grid">
                <label>
                  {t("selection.calendar")}
                  <select value={calendarId} onChange={(event) => setCalendarId(event.target.value)}>
                    <option value="">{t("selection.chooseCalendar")}</option>
                    {options.state.data.calendars.map((calendar) => (
                      <option key={calendar.id} value={calendar.id}>{calendar.id} | {calendar.calendar_version}</option>
                    ))}
                  </select>
                </label>
                <label>
                  {t("selection.session")}
                  <select value={sessionId} disabled={selectedCalendar === null} onChange={(event) => setSessionId(event.target.value)}>
                    <option value="">{t("selection.chooseSession")}</option>
                    {selectedCalendar?.sessions.map((session) => (
                      <option key={session.id} value={session.id}>{session.id} | {session.session_type}</option>
                    ))}
                  </select>
                </label>
                <label>
                  {t("selection.replay")}
                  <select value={replayId} onChange={(event) => setReplayId(event.target.value)}>
                    <option value="">{t("selection.chooseReplay")}</option>
                    {options.state.data.replays.map((replay) => (
                      <option key={replay.replay_id} value={replay.replay_id}>{replay.replay_id} | {replay.status}</option>
                    ))}
                  </select>
                </label>
                <label className="form-grid__wide">{t("selection.instrument")}<input value={instrumentId} onChange={(event) => setInstrumentId(event.target.value)} /></label>
              </div>
              <div className="submission-actions">
                <button className="secondary-button" type="button" disabled={calendarId.length === 0 || calendarDetail.status === "loading"} onClick={() => void loadCalendar()}>
                  {calendarDetail.status === "loading" ? t("selection.loadingCalendar") : t("selection.loadCalendar")}
                </button>
                <button className="secondary-button" type="button" disabled={replayId.length === 0 || replayDetail.status === "loading"} onClick={() => void loadReplay()}>
                  {replayDetail.status === "loading" ? t("selection.loadingReplay") : t("selection.loadReplay")}
                </button>
              </div>
              {calendarDetail.status === "error" ? (
                <StepError error={calendarDetail.error} operation="market_time.calendar.detail" title={t("selection.calendarUnavailable")} retryLabel={t("selection.retryLoad")} onRetry={() => void loadCalendar()} />
              ) : null}
              {replayDetail.status === "error" ? (
                <StepError error={replayDetail.error} operation="market_time.replay.detail" title={t("selection.replayUnavailable")} retryLabel={t("selection.retryLoad")} onRetry={() => void loadReplay()} />
              ) : null}
              {selectedCalendar && selectedReplay ? (
                <dl className="definition-grid definition-grid--wide">
                  <Definition label={t("selection.calendarId")} value={selectedCalendar.calendar.id} />
                  <Definition label={t("selection.calendarVersion")} value={selectedCalendar.calendar.calendar_version} />
                  <Definition label={t("selection.sessionId")} value={selectedSession?.id ?? null} />
                  <Definition label={t("selection.replayId")} value={selectedReplay.session.replay_id} />
                  <Definition label={t("selection.replayStatus")} value={selectedReplay.session.status} />
                  <Definition label={t("selection.streamDigest")} value={selectedReplay.session.cursor.event_stream_digest} />
                  <Definition label={t("selection.cursorPosition")} value={selectedReplay.session.cursor.position} />
                  <Definition label={t("selection.currentEventId")} value={selectedReplay.session.cursor.last_event_id} />
                  <Definition label={t("selection.currentEventTime")} value={selectedReplay.session.cursor.current_event_time} />
                  <Definition label={t("selection.instrumentId")} value={instrumentId.length === 0 ? null : instrumentId} />
                </dl>
              ) : null}
              {selectedReplay && (selectedReplay.session.cursor.position === 0 || selectedReplay.session.cursor.last_event_id === null) ? (
                <p className="form-error" role="alert">{t("selection.replayNoCurrentEvent")}</p>
              ) : null}
            </fieldset>
          </div>
        )}
      </section>

      <section className="content-panel" aria-labelledby="signal-step-title">
        <div className="section-heading">
          <div><p className="eyebrow">{t("signal.eyebrow")}</p><h2 id="signal-step-title">{t("signal.title")}</h2></div>
          <p>{t("signal.description")}</p>
        </div>
        <div className="submission-actions">
          <button className="primary-button" type="button" disabled={signalRequest === null || signalStatus === "pending"} onClick={() => void submitSignal()}>
            {signalStatus === "pending" ? t("signal.pending") : t("signal.action")}
          </button>
          {signalRequest === null ? <p>{t("signal.unavailable")}</p> : null}
        </div>
        {signalError ? <StepError error={signalError} operation="strategy_signal.evaluate" title={t("signal.errorTitle")} retryLabel={t("signal.retry")} onRetry={() => void submitSignal()} /> : null}
        {signalEvidence && !signalAligned ? <p className="form-error" role="status">{t("signal.misaligned")}</p> : null}
        {signalEvidence ? <SignalInspection evidence={signalEvidence} /> : <p className="neutral-note">{t("signal.empty")}</p>}
      </section>

      <section className="content-panel" aria-labelledby="intent-step-title">
        <div className="section-heading">
          <div><p className="eyebrow">{t("intent.eyebrow")}</p><h2 id="intent-step-title">{t("intent.title")}</h2></div>
          <p>{t("intent.description")}</p>
        </div>
        <div className="submission-actions">
          <button className="primary-button" type="button" disabled={intentRequest === null || intentStatus === "pending"} onClick={() => void submitIntent()}>
            {intentStatus === "pending" ? t("intent.pending") : t("intent.action")}
          </button>
          {intentRequest === null ? <p>{t("intent.unavailable")}</p> : null}
        </div>
        {intentError ? <StepError error={intentError} operation="order_intent.create" title={t("intent.errorTitle")} retryLabel={t("intent.retry")} onRetry={() => void submitIntent()} /> : null}
        {intentEvidence && !intentAligned ? <p className="form-error" role="status">{t("intent.misaligned")}</p> : null}
        {intentEvidence ? <IntentInspection evidence={intentEvidence} /> : <p className="neutral-note">{t("intent.empty")}</p>}
      </section>

      <section className="content-panel" aria-labelledby="risk-step-title">
        <div className="section-heading">
          <div><p className="eyebrow">{t("risk.eyebrow")}</p><h2 id="risk-step-title">{t("risk.title")}</h2></div>
          <p>{t("risk.description")}</p>
        </div>
        <fieldset className="form-section strategy-risk-policy">
          <legend>{t("risk.policyTitle")}</legend>
          <div className="form-grid">
            <label>{t("risk.policyId")}<input value="long_only_cash_risk_v1" readOnly /></label>
            <label>{t("risk.pricePolicyId")}<input value="latest_trade_price_v1" readOnly /></label>
            <label>{t("risk.maximumQuantity")}<input value={maximumQuantity} placeholder={t("risk.optional")} onChange={(event) => setMaximumQuantity(event.target.value)} /></label>
            <label>{t("risk.maximumNotional")}<input value={maximumNotional} placeholder={t("risk.optional")} onChange={(event) => setMaximumNotional(event.target.value)} /></label>
          </div>
        </fieldset>
        <div className="submission-actions">
          <button className="primary-button" type="button" disabled={riskRequest === null || riskStatus === "pending"} onClick={() => void submitRisk()}>
            {riskStatus === "pending" ? t("risk.pending") : t("risk.action")}
          </button>
          {riskRequest === null ? <p>{intentEvidence?.response.result_kind === "order_intent_no_action" ? t("risk.noActionUnavailable") : t("risk.unavailable")}</p> : null}
        </div>
        {riskError ? <StepError error={riskError} operation="pre_trade_risk.evaluate" title={t("risk.errorTitle")} retryLabel={t("risk.retry")} onRetry={() => void submitRisk()} /> : null}
        {riskEvidence && !riskAligned ? <p className="form-error" role="status">{t("risk.misaligned")}</p> : null}
        {riskEvidence ? <RiskInspection evidence={riskEvidence} /> : <p className="neutral-note">{t("risk.empty")}</p>}
      </section>

      <aside className="boundary-note" aria-label={t("nonGoalsTitle")}>
        <strong>{t("nonGoalsTitle")}</strong>
        <p>{t("nonGoals")}</p>
      </aside>
      <span className="visually-hidden" aria-live="polite">
        {signalStatus === "pending" || intentStatus === "pending" || riskStatus === "pending"
          ? common("states.loading")
          : ""}
      </span>
    </div>
  );
}
