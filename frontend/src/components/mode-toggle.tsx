"use client"

import { AnimatedThemeToggler } from "@/components/ui/animated-theme-toggler"

export function ModeToggle() {
  return (
    <AnimatedThemeToggler
      className="flex items-center justify-center h-9 w-9 rounded-md  border-input bg-background hover:bg-accent hover:text-accent-foreground"
    />
  )
}