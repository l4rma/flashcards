export default function ProgressBar({ percent }) {
  return (
    <div className="w-full h-2.5 rounded-full bg-progress-track overflow-hidden shadow-[inset_0_1px_2px_rgba(0,0,0,0.06)]">
      <div
        className="h-full rounded-full bg-progress transition-all duration-500"
        style={{ width: `${percent}%` }}
      />
    </div>
  );
}
