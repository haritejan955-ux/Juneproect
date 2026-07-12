export function AttorneyFlagBanner({ show }: { show: boolean }) {
  if (!show) return null;

  return (
    <div
      role="alert"
      className="rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm font-medium text-red-800"
    >
      This claim has been flagged for attorney review due to a high-severity fraud signal or a
      high-risk legal interpretation. This banner cannot be dismissed.
    </div>
  );
}
