"use client";
import { UserButton } from "@clerk/nextjs";
import Link from "next/link";
import { ModeToggle } from "@/components/mode-toggle";

export default function Header() {
  return (
    <header className="sticky top-0 z-50 w-full shadow-lg backdrop-blur-md bg-card/95 border-b border-border">
      <div className="relative container mx-auto px-6 py-4 flex items-center justify-between">
        {/* Logo */}
        <h1 className="text-3xl font-extrabold text-primary tracking-wide font-serif">
          Cryptonizer
        </h1>

        {/* Navigation */}
        <nav className="absolute left-1/2 -translate-x-1/2 flex space-x-6">
          {[
            { href: "/", label: "Home" },
            { href: "/portfolio", label: "Portfolio" },
            { href: "/chatbot", label: "AI Agent" },
          ].map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="px-4 py-2 rounded-lg text-foreground font-semibold transition-all duration-200 hover:bg-accent hover:text-accent-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            >
              {link.label}
            </Link>
          ))}
        </nav>

        {/* Theme Toggle & User button */}
        <div className="flex items-center gap-3">
          <ModeToggle />
          <UserButton afterSignOutUrl="/" />
        </div>
      </div>
    </header>
  );
}
