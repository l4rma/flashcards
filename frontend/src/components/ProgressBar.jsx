export default function ProgressBar({ percent }) {
  return (
    <div className="w-full max-w-sm h-3 rounded-full bg-progress-track overflow-hidden">
      <div
        className="h-full rounded-full bg-progress transition-all duration-500"
        style={{ width: `${percent}%` }}
      />
    </div>
  );
}
