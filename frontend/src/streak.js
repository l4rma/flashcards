// The backend's "gamification day" (streak, daily quests, daily stats)
// rolls over at 3am Europe/Oslo local time, not UTC midnight — see
// stats.py's logical_today for why. Mirrored here so last_active_date
// comparisons agree with the backend's own day boundary; comparing
// against the browser's raw local date, or plain UTC midnight, would
// drift from that and misreport the flame's lit state during the gap.
export function logicalToday() {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Europe/Oslo",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    hour12: false,
  }).formatToParts(new Date());
  const get = (type) => Number(parts.find((p) => p.type === type).value);
  const year = get("year");
  const month = get("month");
  const day = get("day");
  const hour = get("hour") % 24; // midnight can format as "24"

  const osloDate = new Date(Date.UTC(year, month - 1, day));
  if (hour < 3) osloDate.setUTCDate(osloDate.getUTCDate() - 1);
  return osloDate.toISOString().slice(0, 10);
}

export function trainedToday(stats) {
  if (!stats?.last_active_date) return false;
  return stats.last_active_date === logicalToday();
}
