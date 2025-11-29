import { Skeleton, SVGSkeleton } from "./ui/skeleton";

const LoadingSkeleton = () => (
  <>
    <main className="container mx-auto px-4 py-8">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
        <div className="relative p-5 backdrop-blur-2xl border shadow-md from-white/10 dark:from-zinc-800/40 hover:shadow-xl hover:border-primary/40 rounded-xl flex flex-col items-center text-center">
          <span className="absolute -top-3 left-4 px-3 py-1 shadow-sm">
            <Skeleton className="w-[80px] max-w-full" />
          </span>
          <div className="flex justify-center mb-4">
            <SVGSkeleton className="rounded-full shadow-lg transition-transform duration-300 hover:scale-110 w-16 h-16" />
          </div>
          <h2 className="tracking-tight">
            <Skeleton className="w-[56px] max-w-full" />
          </h2>
          <div>
            <Skeleton className="w-[24px] max-w-full" />
          </div>
          <div className="mt-4 mb-2 w-full">
            <div className="tracking-tight flex justify-center">
              <Skeleton className="w-[80px] max-w-full" />
            </div>
            <div className="flex justify-center">
              <span className="inline-block px-3 py-1 mt-2 shadow-sm">
                <Skeleton className="w-[48px] max-w-full" />
              </span>
            </div>
          </div>
          <div className="mt-4 space-y-2 w-full">
            <div className="flex justify-between">
              <span>
                <Skeleton className="w-[88px] max-w-full" />
              </span>
              <span>
                <Skeleton className="w-[64px] max-w-full" />
              </span>
            </div>
          </div>
          <div className="mt-5 w-full">
            <div className="w-full py-2 border hover:from-purple-800/70 tracking-wide flex justify-center">
              <Skeleton className="w-[96px] max-w-full" />
            </div>
          </div>
        </div>
        <div className="relative p-5 backdrop-blur-2xl border shadow-md from-white/10 dark:from-zinc-800/40 hover:shadow-xl hover:border-primary/40 rounded-xl flex flex-col items-center text-center">
          <div className="flex justify-center mb-4">
            <SVGSkeleton className="rounded-full shadow-lg transition-transform duration-300 hover:scale-110 w-16 h-16" />
          </div>
          <h2 className="tracking-tight">
            <Skeleton className="w-[64px] max-w-full" />
          </h2>
          <div>
            <Skeleton className="w-[24px] max-w-full" />
          </div>
          <div className="mt-4 mb-2 w-full">
            <div className="tracking-tight flex justify-center">
              <Skeleton className="w-[72px] max-w-full" />
            </div>
            <div className="flex justify-center">
              <span className="inline-block px-3 py-1 mt-2 shadow-sm">
                <Skeleton className="w-[48px] max-w-full" />
              </span>
            </div>
          </div>
          <div className="mt-4 space-y-2 w-full">
            <div className="flex justify-between">
              <span>
                <Skeleton className="w-[88px] max-w-full" />
              </span>
              <span>
                <Skeleton className="w-[56px] max-w-full" />
              </span>
            </div>
          </div>
          <div className="mt-5 w-full">
            <div className="w-full py-2 border hover:from-purple-800/70 tracking-wide flex justify-center">
              <Skeleton className="w-[96px] max-w-full" />
            </div>
          </div>
        </div>
                <div className="relative p-5 backdrop-blur-2xl border shadow-md from-white/10 dark:from-zinc-800/40 hover:shadow-xl hover:border-primary/40 rounded-xl flex flex-col items-center text-center">
          <div className="flex justify-center mb-4">
            <SVGSkeleton className="rounded-full shadow-lg transition-transform duration-300 hover:scale-110 w-16 h-16" />
          </div>
          <h2 className="tracking-tight">
            <Skeleton className="w-[64px] max-w-full" />
          </h2>
          <div>
            <Skeleton className="w-[24px] max-w-full" />
          </div>
          <div className="mt-4 mb-2 w-full">
            <div className="tracking-tight flex justify-center">
              <Skeleton className="w-[72px] max-w-full" />
            </div>
            <div className="flex justify-center">
              <span className="inline-block px-3 py-1 mt-2 shadow-sm">
                <Skeleton className="w-[48px] max-w-full" />
              </span>
            </div>
          </div>
          <div className="mt-4 space-y-2 w-full">
            <div className="flex justify-between">
              <span>
                <Skeleton className="w-[88px] max-w-full" />
              </span>
              <span>
                <Skeleton className="w-[56px] max-w-full" />
              </span>
            </div>
          </div>
          <div className="mt-5 w-full">
            <div className="w-full py-2 border hover:from-purple-800/70 tracking-wide flex justify-center">
              <Skeleton className="w-[96px] max-w-full" />
            </div>
          </div>
        </div>
                <div className="relative p-5 backdrop-blur-2xl border shadow-md from-white/10 dark:from-zinc-800/40 hover:shadow-xl hover:border-primary/40 rounded-xl flex flex-col items-center text-center">
          <div className="flex justify-center mb-4">
            <SVGSkeleton className="rounded-full shadow-lg transition-transform duration-300 hover:scale-110 w-16 h-16" />
          </div>
          <h2 className="tracking-tight">
            <Skeleton className="w-[64px] max-w-full" />
          </h2>
          <div>
            <Skeleton className="w-[24px] max-w-full" />
          </div>
          <div className="mt-4 mb-2 w-full">
            <div className="tracking-tight flex justify-center">
              <Skeleton className="w-[72px] max-w-full" />
            </div>
            <div className="flex justify-center">
              <span className="inline-block px-3 py-1 mt-2 shadow-sm">
                <Skeleton className="w-[48px] max-w-full" />
              </span>
            </div>
          </div>
          <div className="mt-4 space-y-2 w-full">
            <div className="flex justify-between">
              <span>
                <Skeleton className="w-[88px] max-w-full" />
              </span>
              <span>
                <Skeleton className="w-[56px] max-w-full" />
              </span>
            </div>
          </div>
          <div className="mt-5 w-full">
            <div className="w-full py-2 border hover:from-purple-800/70 tracking-wide flex justify-center">
              <Skeleton className="w-[96px] max-w-full" />
            </div>
          </div>
        </div>
                <div className="relative p-5 backdrop-blur-2xl border shadow-md from-white/10 dark:from-zinc-800/40 hover:shadow-xl hover:border-primary/40 rounded-xl flex flex-col items-center text-center">
          <div className="flex justify-center mb-4">
            <SVGSkeleton className="rounded-full shadow-lg transition-transform duration-300 hover:scale-110 w-16 h-16" />
          </div>
          <h2 className="tracking-tight">
            <Skeleton className="w-[64px] max-w-full" />
          </h2>
          <div>
            <Skeleton className="w-[24px] max-w-full" />
          </div>
          <div className="mt-4 mb-2 w-full">
            <div className="tracking-tight flex justify-center">
              <Skeleton className="w-[72px] max-w-full" />
            </div>
            <div className="flex justify-center">
              <span className="inline-block px-3 py-1 mt-2 shadow-sm">
                <Skeleton className="w-[48px] max-w-full" />
              </span>
            </div>
          </div>
          <div className="mt-4 space-y-2 w-full">
            <div className="flex justify-between">
              <span>
                <Skeleton className="w-[88px] max-w-full" />
              </span>
              <span>
                <Skeleton className="w-[56px] max-w-full" />
              </span>
            </div>
          </div>
          <div className="mt-5 w-full">
            <div className="w-full py-2 border hover:from-purple-800/70 tracking-wide flex justify-center">
              <Skeleton className="w-[96px] max-w-full" />
            </div>
          </div>
        </div>
                <div className="relative p-5 backdrop-blur-2xl border shadow-md from-white/10 dark:from-zinc-800/40 hover:shadow-xl hover:border-primary/40 rounded-xl flex flex-col items-center text-center">
          <div className="flex justify-center mb-4">
            <SVGSkeleton className="rounded-full shadow-lg transition-transform duration-300 hover:scale-110 w-16 h-16" />
          </div>
          <h2 className="tracking-tight">
            <Skeleton className="w-[64px] max-w-full" />
          </h2>
          <div>
            <Skeleton className="w-[24px] max-w-full" />
          </div>
          <div className="mt-4 mb-2 w-full">
            <div className="tracking-tight flex justify-center">
              <Skeleton className="w-[72px] max-w-full" />
            </div>
            <div className="flex justify-center">
              <span className="inline-block px-3 py-1 mt-2 shadow-sm">
                <Skeleton className="w-[48px] max-w-full" />
              </span>
            </div>
          </div>
          <div className="mt-4 space-y-2 w-full">
            <div className="flex justify-between">
              <span>
                <Skeleton className="w-[88px] max-w-full" />
              </span>
              <span>
                <Skeleton className="w-[56px] max-w-full" />
              </span>
            </div>
          </div>
          <div className="mt-5 w-full">
            <div className="w-full py-2 border hover:from-purple-800/70 tracking-wide flex justify-center">
              <Skeleton className="w-[96px] max-w-full" />
            </div>
          </div>
        </div>
                <div className="relative p-5 backdrop-blur-2xl border shadow-md from-white/10 dark:from-zinc-800/40 hover:shadow-xl hover:border-primary/40 rounded-xl flex flex-col items-center text-center">
          <div className="flex justify-center mb-4">
            <SVGSkeleton className="rounded-full shadow-lg transition-transform duration-300 hover:scale-110 w-16 h-16" />
          </div>
          <h2 className="tracking-tight">
            <Skeleton className="w-[64px] max-w-full" />
          </h2>
          <div>
            <Skeleton className="w-[24px] max-w-full" />
          </div>
          <div className="mt-4 mb-2 w-full">
            <div className="tracking-tight flex justify-center">
              <Skeleton className="w-[72px] max-w-full" />
            </div>
            <div className="flex justify-center">
              <span className="inline-block px-3 py-1 mt-2 shadow-sm">
                <Skeleton className="w-[48px] max-w-full" />
              </span>
            </div>
          </div>
          <div className="mt-4 space-y-2 w-full">
            <div className="flex justify-between">
              <span>
                <Skeleton className="w-[88px] max-w-full" />
              </span>
              <span>
                <Skeleton className="w-[56px] max-w-full" />
              </span>
            </div>
          </div>
          <div className="mt-5 w-full">
            <div className="w-full py-2 border hover:from-purple-800/70 tracking-wide flex justify-center">
              <Skeleton className="w-[96px] max-w-full" />
            </div>
          </div>
        </div>
        <div className="relative p-5 backdrop-blur-2xl border shadow-md from-white/10 dark:from-zinc-800/40 hover:shadow-xl hover:border-primary/40 rounded-xl flex flex-col items-center text-center">
          <div className="flex justify-center mb-4">
            <SVGSkeleton className="rounded-full shadow-lg transition-transform duration-300 hover:scale-110 w-16 h-16" />
          </div>
          <h2 className="tracking-tight">
            <Skeleton className="w-[48px] max-w-full" />
          </h2>
          <div>
            <Skeleton className="w-[32px] max-w-full" />
          </div>
          <div className="mt-4 mb-2 w-full">
            <div className="tracking-tight flex justify-center">
              <Skeleton className="w-[40px] max-w-full" />
            </div>
            <div className="flex justify-center">
              <span className="inline-block px-3 py-1 mt-2 shadow-sm">
                <Skeleton className="w-[40px] max-w-full" />
              </span>
            </div>
          </div>
          <div className="mt-4 space-y-2 w-full">
            <div className="flex justify-between">
              <span>
                <Skeleton className="w-[88px] max-w-full" />
              </span>
              <span>
                <Skeleton className="w-[56px] max-w-full" />
              </span>
            </div>
          </div>
          <div className="mt-5 w-full">
            <div className="w-full py-2 border hover:from-purple-800/70 tracking-wide flex justify-center">
              <Skeleton className="w-[96px] max-w-full" />
            </div>
          </div>
        </div>
        <div className="relative p-5 backdrop-blur-2xl border shadow-md from-white/10 dark:from-zinc-800/40 hover:shadow-xl hover:border-primary/40 rounded-xl flex flex-col items-center text-center">
          <div className="flex justify-center mb-4">
            <SVGSkeleton className="rounded-full shadow-lg transition-transform duration-300 hover:scale-110 w-16 h-16" />
          </div>
          <h2 className="tracking-tight">
            <Skeleton className="w-[24px] max-w-full" />
          </h2>
          <div>
            <Skeleton className="w-[24px] max-w-full" />
          </div>
          <div className="mt-4 mb-2 w-full">
            <div className="tracking-tight flex justify-center">
              <Skeleton className="w-[40px] max-w-full" />
            </div>
            <div className="flex justify-center">
              <span className="inline-block px-3 py-1 mt-2 shadow-sm">
                <Skeleton className="w-[40px] max-w-full" />
              </span>
            </div>
          </div>
          <div className="mt-4 space-y-2 w-full">
            <div className="flex justify-between">
              <span>
                <Skeleton className="w-[88px] max-w-full" />
              </span>
              <span>
                <Skeleton className="w-[56px] max-w-full" />
              </span>
            </div>
          </div>
          <div className="mt-5 w-full">
            <div className="w-full py-2 border hover:from-purple-800/70 tracking-wide flex justify-center">
              <Skeleton className="w-[96px] max-w-full" />
            </div>
          </div>
        </div>
        <div className="relative p-5 backdrop-blur-2xl border shadow-md from-white/10 dark:from-zinc-800/40 hover:shadow-xl hover:border-primary/40 rounded-xl flex flex-col items-center text-center">
          <div className="flex justify-center mb-4">
            <SVGSkeleton className="rounded-full shadow-lg transition-transform duration-300 hover:scale-110 w-16 h-16" />
          </div>
          <h2 className="tracking-tight">
            <Skeleton className="w-[24px] max-w-full" />
          </h2>
          <div>
            <Skeleton className="w-[24px] max-w-full" />
          </div>
          <div className="mt-4 mb-2 w-full">
            <div className="tracking-tight flex justify-center">
              <Skeleton className="w-[56px] max-w-full" />
            </div>
            <div className="flex justify-center">
              <span className="inline-block px-3 py-1 mt-2 shadow-sm">
                <Skeleton className="w-[48px] max-w-full" />
              </span>
            </div>
          </div>
          <div className="mt-4 space-y-2 w-full">
            <div className="flex justify-between">
              <span>
                <Skeleton className="w-[88px] max-w-full" />
              </span>
              <span>
                <Skeleton className="w-[56px] max-w-full" />
              </span>
            </div>
          </div>
          <div className="mt-5 w-full">
            <div className="w-full py-2 border hover:from-purple-800/70 tracking-wide flex justify-center">
              <Skeleton className="w-[96px] max-w-full" />
            </div>
          </div>
        </div>
      </div>
    </main>
  </>
);

const SandboxPreview = () => (
  <div className="flex justify-center w-full h-full p-10">
    <LoadingSkeleton />
  </div>
);

export default SandboxPreview;
