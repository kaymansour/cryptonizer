import { Skeleton, SVGSkeleton } from "./ui/skeleton";

const LoadingSkeleton = () => (
  <>
    <div className="container mx-auto px-4 max-w-7xl">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 p-6 backdrop-blur-xl border border-border rounded-xl mb-8">
        <div className="flex items-center gap-4">
          <div className="relative">
            <SVGSkeleton className="rounded-full shadow-lg border-2 border-border w-16 h-16" />
            <div className="absolute -bottom-1 -right-1 h-6 w-6 border-2 border-background rounded-full flex items-center justify-center bg-background">
              <SVGSkeleton className="w-3 h-3" />
            </div>
          </div>
          <div>
            <h1>
              <Skeleton className="w-[64px] max-w-full" />
            </h1>
            <div className="flex items-center gap-3 mt-1">
              <span>
                <Skeleton className="w-[24px] max-w-full" />
              </span>
              <span className="px-2 py-1">
                <Skeleton className="w-[48px] max-w-full" />
              </span>
            </div>
          </div>
        </div>
        <div className="text-right">
          <div>
            <Skeleton className="w-[72px] max-w-full" />
          </div>
          <div className="mt-1">
            <Skeleton className="w-[136px] max-w-full" />
          </div>
        </div>
      </div>
      <div className="grid w-full auto-rows-[22rem] grid-cols-3 gap-4 lg:grid-rows-2 mb-8">
        <div className="relative col-span-3 flex flex-col justify-between transform-gpu dark:[border:1px_solid_rgba(255,255,255,.1)] lg:col-start-1 lg:col-end-3 lg:row-start-1 lg:row-end-2 border-primary/40 rounded-xl overflow-hidden">
          <div>
            <div className="absolute from-primary/10"></div>
          </div>
          <div className="p-4 flex flex-col h-full">
            <div className="z-10 flex transform-gpu flex-col gap-1 lg:group-hover:-translate-y-2">
              <SVGSkeleton className="lucide-chart-column origin-left transform-gpu group-hover:scale-75 w-[24px] h-[24px]" />
              <h3>
                <Skeleton className="w-[88px] max-w-full" />
              </h3>
              <div className="max-w-lg">
                <Skeleton className="w-[208px] max-w-full" />
              </div>
            </div>
            <div className="mt-auto flex-1">
              <div className="relative z-10 h-80 mt-4">
                <canvas height="320" width="780"></canvas>
              </div>
            </div>
          </div>
          <div className="absolute transform-gpu group-hover:bg-black/3 group-hover:dark:bg-neutral-800/10"></div>
        </div>
        <div className="relative col-span-3 flex flex-col justify-between transform-gpu dark:[border:1px_solid_rgba(255,255,255,.1)] lg:col-start-3 lg:col-end-4 lg:row-start-1 lg:row-end-2 border-primary/40 rounded-xl overflow-hidden">
          <div>
            <div className="absolute from-primary/10"></div>
          </div>
          <div className="p-4 flex flex-col h-full">
            <div className="z-10 flex transform-gpu flex-col gap-1 lg:group-hover:-translate-y-2">
              <SVGSkeleton className="origin-left transform-gpu group-hover:scale-75 w-[24px] h-[24px]" />
              <h3>
                <Skeleton className="w-[136px] max-w-full" />
              </h3>
              <div className="max-w-lg">
                <Skeleton className="w-[144px] max-w-full" />
              </div>
            </div>
            <div className="mt-auto flex-1">
              <div className="relative z-10 space-y-4 mt-4">
                <div className="flex justify-between items-center py-2 border-b border-border">
                  <span>
                    <Skeleton className="w-[80px] max-w-full" />
                  </span>
                  <span>
                    <Skeleton className="w-[56px] max-w-full" />
                  </span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-border">
                  <span>
                    <Skeleton className="w-[80px] max-w-full" />
                  </span>
                  <span>
                    <Skeleton className="w-[48px] max-w-full" />
                  </span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-border">
                  <span>
                    <Skeleton className="w-[80px] max-w-full" />
                  </span>
                  <span>
                    <Skeleton className="w-[48px] max-w-full" />
                  </span>
                </div>
                <div className="flex justify-between items-center py-2">
                  <span>
                    <Skeleton className="w-[88px] max-w-full" />
                  </span>
                  <span>
                    <Skeleton className="w-[16px] max-w-full" />
                  </span>
                </div>
              </div>
            </div>
          </div>
          <div className="absolute transform-gpu group-hover:bg-black/3 group-hover:dark:bg-neutral-800/10"></div>
        </div>
        <div className="relative col-span-3 flex flex-col justify-between transform-gpu dark:[border:1px_solid_rgba(255,255,255,.1)] lg:col-start-1 lg:col-end-4 lg:row-start-2 lg:row-end-3 border-primary/40 rounded-xl overflow-hidden">
          <div>
            <div className="absolute from-primary/10"></div>
          </div>
          <div className="p-4 flex flex-col h-full">
            <div className="z-10 flex transform-gpu flex-col gap-1 lg:group-hover:-translate-y-2">
              <SVGSkeleton className="origin-left transform-gpu group-hover:scale-75 w-[24px] h-[24px]" />
              <h3>
                <Skeleton className="w-[112px] max-w-full" />
              </h3>
              <div className="max-w-lg">
                <Skeleton className="w-2xs max-w-full" />
              </div>
            </div>
            <div className="mt-auto flex-1">
              <div className="relative z-10 mt-4">
                <div className="w-full flex justify-between items-center text-left mb-4">
                  <span>
                    <Skeleton className="w-[96px] max-w-full" />
                  </span>
                  <div className="p-2 group-hover:bg-accent">
                    <SVGSkeleton className="w-[20px] h-[20px]" />
                  </div>
                </div>
                <div className="max-h-0">
                  <div className="max-w-none">
                    <div className="leading-relaxed">
                      <Skeleton className="w-[21904px] max-w-full" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div className="absolute transform-gpu group-hover:bg-black/3 group-hover:dark:bg-neutral-800/10"></div>
        </div>
      </div>
    </div>
  </>
);

const SandboxPreview = () => (
  <div className="flex justify-center w-full h-full p-10">
    <LoadingSkeleton />
  </div>
);

export default SandboxPreview;
