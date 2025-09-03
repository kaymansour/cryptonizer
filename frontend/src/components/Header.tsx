"use client";
import { UserButton } from "@clerk/nextjs";

export default function Header() {
  return (
    <div className="w-full shadow-lg py-4 px-6 bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900">
      <div className="container mx-auto flex flex-col sm:flex-row justify-between items-center gap-4">
        {/* Logo */}
        <h1 className="text-3xl font-extrabold text-cyan-400 tracking-wide drop-shadow-lg">
          Crypto
        </h1>

        {/* Navigation */}
        <nav className="flex-1 flex justify-center space-x-6 flex-wrap">
          <a href="/" className="px-4 py-2 rounded-lg text-gray-200 font-semibold hover:text-lg">
            Home
          </a>
          <a href="/predicts" className="px-4 py-2 rounded-lg text-gray-200 font-semibold hover:text-lg">
            Predict
          </a>
          <a href="/about" className="px-4 py-2 rounded-lg text-gray-200 font-semibold hover:text-lg">
            About
          </a>
          <a href="/chatbot" className="px-4 py-2 rounded-lg text-gray-200 font-semibold hover:text-lg">
            AI Agent
          </a>
        </nav>

        {/* User Button */}
        <UserButton afterSignOutUrl="/" />
      </div>
    </div>
  );
}
