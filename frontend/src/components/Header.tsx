"use client";
import { UserButton, SignedIn, SignedOut, SignInButton } from "@clerk/nextjs";
import Link from "next/link";
import { ModeToggle } from "@/components/mode-toggle";
import { Button } from "@/components/ui/button";

export default function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/80 backdrop-blur-xl">
      <div className="container mx-auto px-6 py-4 flex items-center justify-between">
        
        {/* Logo */}
        <Link 
          href="/" 
          className="text-3xl font-extrabold tracking-tight text-foreground leading-none"
        >
          Cryptonizer
        </Link>

        {/* Navigation - CENTERED */}
        <nav className="hidden md:flex items-center gap-10 absolute left-1/2 transform -translate-x-1/2">
          {[
            { href: "/dashboard", label: "Home" },
            { href: "/portfolio", label: "Portfolio" },
            { href: "/saved", label: "Saved Results" },
          ].map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="
                text-sm font-semibold tracking-wide relative
                text-muted-foreground transition-all duration-300
                hover:text-purple-500
              "
            >
              {link.label}

              {/* Purple underline animation */}
              <span
                className="
                  absolute left-0 -bottom-1 h-[2px] w-0 bg-purple-500 
                  transition-all duration-300
                  hover:w-full
                "
              ></span>
            </Link>
          ))}
        </nav>

        {/* Theme & User */}
        <div className="flex items-center gap-4">
          <ModeToggle />
          <SignedIn>
            <UserButton afterSignOutUrl="/" />
          </SignedIn>
          <SignedOut>
            <SignInButton mode="modal">
              <Button variant="outline" size="sm" className="rounded-xl">
                Sign in
              </Button>
            </SignInButton>
          </SignedOut>
        </div>
      </div>
    </header>
  );
}
