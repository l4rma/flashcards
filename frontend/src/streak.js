// Whether today's training has already happened, per the backend's own
// notion of "today" (Lambda runs in UTC, and stats.py's streak logic is
// anchored to date.today() there — comparing against the browser's local
// date would drift from that and misreport the flame's lit state around
// midnight in non-UTC timezones).
export function trainedToday(stats) {
  if (!stats?.last_active_date) return false;
  const todayUTC = new Date().toISOString().slice(0, 10);
  return stats.last_active_date === todayUTC;
}
