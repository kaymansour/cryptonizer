"use client";
import { UserButton } from "@clerk/nextjs";
import Link from "next/link";

/**
 * Header component for the app
 * - Shows the logo
 * - Displays navigation links
 * - Includes the user account button (login/logout)
 */
export default function Header() {
  return (
    // Header container with gradient background and shadow
    <div className="w-full shadow-lg py-4 px-6 bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900">
      {/* Inner container to center content and manage spacing */}
      <div className="container mx-auto flex flex-col sm:flex-row justify-between items-center gap-4">

        {/* Logo */}
        <h1 className="text-3xl font-extrabold text-cyan-400 tracking-wide drop-shadow-lg">
          Cryptonizer
        </h1>

        {/* Navigation links */}
        <nav className="flex-1 flex justify-center space-x-6">
          <Link
            href="/"
            className="px-4 py-2 rounded-lg text-gray-200 font-semibold hover:text-lg"
          >
            Home
          </Link>
          <Link
            href="/portfolio"
            className="px-4 py-2 rounded-lg text-gray-200 font-semibold transition-all duration-200 hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-cyan-400 hover:text-lg"
          >
            Portfolio
          </Link>
          <Link
            href="/predicts"
            className="px-4 py-2 rounded-lg text-gray-200 font-semibold hover:text-lg"
          >
            Predict
          </Link>
          
          <Link
            href="/chatbot"
            className="px-4 py-2 rounded-lg text-gray-200 font-semibold hover:text-lg"
          >
            AI Agent
          </Link>
        </nav>

        {/* User button from Clerk (login/logout) */}
        <UserButton afterSignOutUrl="/" />
      </div>
    </div>
  );
}
