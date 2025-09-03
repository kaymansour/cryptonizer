export const formatNumber = (num: number) => {
  if (num >= 1e9) return (num / 1e9).toFixed(1) + "B";
  if (num >= 1e6) return (num / 1e6).toFixed(1) + "M";
  if (num >= 1e3) return (num / 1e3).toFixed(1) + "K";
  return num.toFixed(2);
};

export const convertPrice = (priceUsd: number, currency: "usd" | "bhd") => {
  if (currency === "bhd") return priceUsd * 0.376; // USD → BHD
  return priceUsd; // USD default
};
