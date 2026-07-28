import { TradingCalendarDetailView } from "@/components/trading-calendar-detail-view";
import { WorkspaceShell } from "@/components/workspace-shell";

export default async function TradingCalendarDetailPage({
  params,
}: {
  params: Promise<{ calendarId: string }>;
}) {
  const { calendarId } = await params;
  return (
    <WorkspaceShell>
      <TradingCalendarDetailView calendarId={calendarId} />
    </WorkspaceShell>
  );
}
