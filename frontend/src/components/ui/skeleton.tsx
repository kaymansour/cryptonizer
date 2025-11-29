const Skeleton = ({ className }: { className?: string }) => (
  <div aria-live="polite" aria-busy="true" className={className}>
    <span
      className="
        inline-flex w-full animate-pulse select-none rounded-md
        bg-gray-200 dark:bg-gray-800 leading-none
      "
    >
      ‌
    </span>
  </div>
);

const SVGSkeleton = ({ className }: { className?: string }) => (
  <svg
    className={
      className +
      " animate-pulse rounded bg-gray-200 dark:bg-gray-800"
    }
  />
);

export { Skeleton, SVGSkeleton };
