import * as React from "react";

function cn(...classes: (string | undefined)[]) {
  return classes.filter(Boolean).join(' ');
}

export interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value?: number;
  max?: number;
}

const Progress = React.forwardRef<HTMLDivElement, ProgressProps>(
  ({ className, value = 0, max = 100, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "relative h-4 w-full overflow-hidden rounded-full bg-gray-300/50 shadow-inner",
        className
      )}
      {...props}
    >
      <div
        className="h-full bg-gradient-to-r from-blue-400 to-blue-600 shadow-md transition-all duration-500 ease-out"
        style={{ width: `${(value / max) * 100}%` }}
      />
    </div>
  )
);

Progress.displayName = "Progress";

export { Progress };
