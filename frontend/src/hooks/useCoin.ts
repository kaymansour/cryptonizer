import { useState, useEffect } from 'react';
import { Coin } from '@/types/Coin';

export const useCoin = (id: string | null) => {
  const [coin, setCoin] = useState<Coin | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!id) {
      setError('No coin ID provided');
      setLoading(false);
      return;
    }

    const fetchCoin = async () => {
      try {
        const response = await fetch(`/api/coin?id=${id}`);
        if (!response.ok) throw new Error('Failed to fetch coin');
        const data = await response.json();
        setCoin(data);
      } catch (err) {
        setError('Failed to fetch coin details');
      } finally {
        setLoading(false);
      }
    };

    fetchCoin();
  }, [id]);

  return { coin, loading, error };
};