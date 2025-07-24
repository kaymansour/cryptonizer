// src/components/TopBanner.tsx

interface TopBannerProps {
  onSearch: (symbol: string) => void;
}

export default function TopBanner({ onSearch }: TopBannerProps) {
  return (
    <div className="bg-indigo-800 px-6 py-4">
      <div className="container mx-auto flex items-center justify-center">
        <input
          type="text"
          placeholder="Search for a cryptocurrency..."
          className="w-full max-w-md px-4 py-2 rounded-md bg-gray-900 text-white placeholder-gray-400"
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              const target = e.target as HTMLInputElement;
              if (target.value.trim()) {
                onSearch(target.value.trim());
              }
            }
          }}
        />
      </div>
    </div>
  );
}
