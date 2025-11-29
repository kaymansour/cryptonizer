import * as React from "react"

function cn(...classes: (string | undefined)[]) {
  return classes.filter(Boolean).join(" ")
}

type CheckboxProps = Omit<React.InputHTMLAttributes<HTMLInputElement>, "type">

const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className, ...props }, ref) => (
    <label className="relative inline-flex items-center cursor-pointer">
      <input
        type="checkbox"
        className={cn(
          "peer absolute w-0 h-0 opacity-0",
          className
        )}
        ref={ref}
        {...props}
      />
      <span
        className={cn(
          "h-6 w-6 flex items-center justify-center rounded-xl border border-gray-400 bg-gray-800/20 backdrop-blur-sm shadow-inner transition-all duration-300 " +
          "peer-checked:bg-gradient-to-tr peer-checked:from-blue-500 peer-checked:to-purple-500 peer-checked:border-transparent " +
          "hover:shadow-lg hover:shadow-gray-700/40"
        )}
      >
        <svg
          className="h-4 w-4 text-white opacity-0 peer-checked:opacity-100 transition-opacity duration-300"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <polyline points="20 6 9 17 4 12" />
        </svg>
      </span>
    </label>
  )
)

Checkbox.displayName = "Checkbox"

export { Checkbox }
