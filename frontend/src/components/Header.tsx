"use client";

import { UserButton } from "@clerk/nextjs";

export default function Header() {
  return (
    <header className="w-full bg-indigo-950 shadow-lg py-4 px-6">
      <div className="container mx-auto flex justify-between items-center">
        <h1 className="text-xl font-bold text-cyan-400">Crypto Dashboard</h1>

        {/* Clerk User Profile Button */}
        <UserButton afterSignOutUrl="/" />
      </div>
    </header>
  );
}
