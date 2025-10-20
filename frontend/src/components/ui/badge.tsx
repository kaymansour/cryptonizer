import * as React from "react"

function cn(...classes: (string | undefined)[]) {
  return classes.filter(Boolean).join(" ")
}

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "secondary" | "destructive" | "outline"
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  const variantClasses = {
    default:
      "bg-blue-600/40 backdrop-blur-xl text-white border border-blue-500/30 shadow-lg shadow-blue-500/20 hover:bg-blue-600/60 hover:shadow-xl hover:shadow-blue-500/40",
    secondary:
      "bg-gray-700/40 backdrop-blur-xl text-white border border-gray-600/30 shadow-md shadow-gray-400/20 hover:bg-gray-700/60 hover:shadow-lg hover:shadow-gray-500/30",
    destructive:
      "bg-red-600/40 backdrop-blur-xl text-white border border-red-500/30 shadow-lg shadow-red-500/20 hover:bg-red-600/60 hover:shadow-xl hover:shadow-red-500/40",
    outline:
      "bg-transparent border border-gray-500 text-gray-200 shadow-sm hover:bg-gray-800/20 hover:shadow-md",
  }

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors",
        variantClasses[variant] ?? variantClasses.default,
        className
      )}
      {...props}
    />
  )
}

export { Badge }
