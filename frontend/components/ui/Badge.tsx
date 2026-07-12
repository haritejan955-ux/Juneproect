const VARIANT_CLASSES = {
  green: "bg-green-100 text-green-800 border-green-300",
  amber: "bg-amber-100 text-amber-800 border-amber-300",
  red: "bg-red-100 text-red-800 border-red-300",
  gray: "bg-slate-100 text-slate-700 border-slate-300",
} as const;

interface BadgeProps {
  variant: keyof typeof VARIANT_CLASSES;
  children: React.ReactNode;
}

export function Badge({ variant, children }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-3 py-1 text-sm font-medium ${VARIANT_CLASSES[variant]}`}
    >
      {children}
    </span>
  );
}
