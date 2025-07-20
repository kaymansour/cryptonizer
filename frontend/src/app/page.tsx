'use client'

import { useEffect } from 'react'
import { SignedIn, SignedOut, SignInButton, UserButton } from '@clerk/nextjs'

export default function Home() {
  // This checks connection silently
  useEffect(() => {
    fetch("http://localhost:8000/api/status")
      .then((res) => res.json())
      .then((data) => {
        console.log("✅ Backend connected:", data.message)
      })
      .catch((err) => {
        console.error("❌ Backend connection failed", err)
      })
  }, [])

  return (
    <main className="min-h-screen p-10 bg-gray-100 flex flex-col items-center justify-center space-y-6 text-center">
      <SignedOut>
        <h1 className="text-2xl font-bold text-gray-800">Welcome to the Crypto App</h1>
        <SignInButton>
          <button className="mt-4 px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition">
            Sign In
          </button>
        </SignInButton>
      </SignedOut>

      <SignedIn>
        <div className="flex flex-col items-center space-y-4">
          <h2 className="text-2xl font-semibold text-green-700">You are logged in</h2>
          <UserButton afterSignOutUrl="/" />
        </div>
      </SignedIn>
    </main>
  )
}
