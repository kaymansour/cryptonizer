"use client";
import { UserButton } from "@clerk/nextjs";
import Link from "next/link";
import { ModeToggle } from "@/components/mode-toggle";

export default function Header() {
  return (
    <header className="w-full shadow-lg py-4 px-6 bg-card border-b border-border">

      <div className="container mx-auto flex flex-col sm:flex-row justify-between items-center gap-4">
        
        {/* Logo */}
        <h1 className="text-3xl font-extrabold text-primary tracking-wide">
          Cryptonizer
        </h1>

        {/* Navigation */}
        <nav className="flex-1 flex justify-center space-x-6">
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
