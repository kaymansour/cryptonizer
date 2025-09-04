interface TopBannerProps {
  onSearch: (symbol: string) => void;
}

export default function TopBanner({ onSearch }: TopBannerProps) {
  return (
    <div className="mt-32 px-6 py-4">
      <h1 className="text-4xl font-bold text-center text-white mb-4">
        Cryptocurrency Price Prediction
      </h1>
      <p className="text-center text-gray-400 mb-2">
        Enter a cryptocurrency symbol to get started
      </p>
      <div className="container mx-auto flex items-center justify-center rounded-lg p-4 ">
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
        <button
          className="ml-4 px-4 py-2 bg-cyan-500 text-white rounded-md hover:bg-cyan-600"
          onClick={() => {
            const input = document.querySelector("input") as HTMLInputElement;
            if (input.value.trim()) {
              onSearch(input.value.trim());
            }
          }}

        >
          Search
        </button>
      </div>
    </div>
  );
}
