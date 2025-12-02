import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server"

// Public routes: homepage, sign-in, and sign-up pages.
const isPublicRoute = createRouteMatcher(["/", "/sign-in(.*)", "/sign-up(.*)"])

export default clerkMiddleware(async (auth, req) => {
  if (!isPublicRoute(req)) {
    const signInUrl = new URL("/sign-in", req.url)
    signInUrl.searchParams.set("message", "You should sign up first")

    await auth.protect({
      unauthenticatedUrl: signInUrl.toString(),
      unauthorizedUrl: signInUrl.toString(),
    })
  }
})

// Match all routes except static assets and Next internals.
export const config = {
  matcher: [
    // Skip Next.js internals and all static files, unless found in search params
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    // Always run for API routes
    '/(api|trpc)(.*)',
  ],
}
