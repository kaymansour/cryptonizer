import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const id = searchParams.get('id');

  if (!id) {
    return NextResponse.json({ error: 'Coin ID required' }, { status: 400 });
  }

  try {
    const response = await fetch(
      `https://api.coingecko.com/api/v3/coins/${id}?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false&sparkline=false`
    );
    
    if (!response.ok) {
      throw new Error('CoinGecko API error');
    }

    const data = await response.json();
    

    const coin = {
      id: data.id,
      name: data.name,
      symbol: data.symbol,
      image: data.image.large,
      current_price: data.market_data.current_price.usd,
      market_cap: data.market_data.market_cap.usd,
      total_volume: data.market_data.total_volume.usd,
      price_change_percentage_24h: data.market_data.price_change_percentage_24h,
    };

    return NextResponse.json(coin);
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to fetch coin' },
      { status: 500 }
    );
  }
}