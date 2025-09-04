"use client";
import { UserButton } from "@clerk/nextjs";

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
          Crypto
        </h1>

        {/* Navigation links */}
        <nav className="flex-1 flex justify-center space-x-6 flex-wrap">
          <a
            href="/"
            className="px-4 py-2 rounded-lg text-gray-200 font-semibold hover:text-lg"
          >
            Home
          </a>
          <a
            href="/predicts"
            className="px-4 py-2 rounded-lg text-gray-200 font-semibold hover:text-lg"
          >
            Predict
          </a>
          <a
            href="/about"
            className="px-4 py-2 rounded-lg text-gray-200 font-semibold hover:text-lg"
          >
            About
          </a>
          <a
            href="/chatbot"
            className="px-4 py-2 rounded-lg text-gray-200 font-semibold hover:text-lg"
          >
            AI Agent
          </a>
        </nav>

        {/* User button from Clerk (login/logout) */}
        <UserButton afterSignOutUrl="/" />
      </div>
    </div>
  );
}
