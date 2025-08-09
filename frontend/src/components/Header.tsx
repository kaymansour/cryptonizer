"use client";

import { UserButton } from "@clerk/nextjs";

export default function Header() {
  return (
    <div className="w-full shadow-lg py-4 px-6 bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900">
      <div className="container mx-auto flex justify-between items-center">
        <h1 className="text-3xl font-extrabold text-cyan-400 tracking-wide drop-shadow-lg">
          Crypto
        </h1>
        <nav className="flex-1 flex justify-center space-x-6">
          <a
            href="/"
            className="px-4 py-2 rounded-lg text-gray-200 font-semibold transition-all duration-200 hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-cyan-400 hover:text-lg"
          >
            Home
          </a>
          <a
            href="/about"
            className="px-4 py-2 rounded-lg text-gray-200 font-semibold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-cyan-400 hover:text-lg"
          >
            About
          </a>
          <a
            href="/chatbot"
            className="px-4 py-2 rounded-lg text-gray-200  font-semibold transition-colors duration-200  focus:outline-none focus:ring-2 focus:ring-cyan-400 hover:text-lg"
          >
          Ai agent
          </a>
        </nav>
        <div className="ml-6">
          <UserButton afterSignOutUrl="/" />
        </div>
      </div>
    </div>
  );
}
