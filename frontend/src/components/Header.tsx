"use client";
import { UserButton } from "@clerk/nextjs";
import Link from "next/link";

export default function Header() {
  return (
    <header className="w-full shadow-lg py-4 px-6 bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900">

      <div className="container mx-auto flex flex-col sm:flex-row justify-between items-center gap-4">
        
        {/* Logo */}
        <h1 className="text-3xl font-extrabold text-cyan-400 tracking-wide drop-shadow-lg">
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
              className="px-4 py-2 rounded-lg text-gray-200 font-semibold transition-all duration-200 hover:text-lg hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-cyan-400"
            >
              {link.label}
            </Link>
          ))}
        </nav>

        {/* User button */}
        <UserButton afterSignOutUrl="/" />
      </div>
    </header>
  );
}
