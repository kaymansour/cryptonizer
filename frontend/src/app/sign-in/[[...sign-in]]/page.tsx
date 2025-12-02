"use client";

import { SignIn } from "@clerk/nextjs";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

function SignInContent() {
  const searchParams = useSearchParams();
  const message = searchParams.get("message");

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-6 py-12">
      
      {/* Main Wrapper */}
      <div className="w-full max-w-md bg-card border border-border rounded-3xl shadow-xl p-8 backdrop-blur-md">
        
        {/* Title */}
        <h1 className="text-3xl font-bold text-center mb-6">
          Welcome Back to{" "}
          <span className="bg-linear-to-r from-primary via-purple-500 to-pink-500 bg-clip-text text-transparent">
            Cryptonizer
          </span>
        </h1>

        {/* Message Box */}
{message && (
  <div className="mb-6 rounded-xl bg-linear-to-r from-primary/20 via-purple-500/20 to-pink-500/20 border border-primary/30 px-6 py-4 text-center shadow-sm">
    <p className="text-md font-semibold bg-linear-to-r from-primary to-pink-500 bg-clip-text text-transparent">
      {decodeURIComponent(message)}
    </p>
  </div>
)}


        {/* Clerk SignIn Component */}
        <div className="flex justify-center">
          <SignIn
            appearance={{
              elements: {
                card: "bg-transparent shadow-none",
                formButtonPrimary:
                  "bg-primary hover:bg-primary/90 text-white font-semibold rounded-xl",
                headerTitle: "text-foreground",
                headerSubtitle: "text-muted-foreground",
                socialButtonsBlockButton:
                  "bg-card border border-border text-foreground hover:bg-accent",
                formFieldInput:
                  "bg-background border border-border rounded-xl text-foreground",
                footerActionText: "text-muted-foreground",
                footerActionLink:
                  "text-primary hover:text-primary/90 font-semibold",
              },
            }}
          />
        </div>
      </div>
    </div>
  );
}

export default function SignInPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-background">
          <div className="text-lg text-muted-foreground animate-pulse">
            Loading...
          </div>
        </div>
      }
    >
      <SignInContent />
    </Suspense>
  );
}
