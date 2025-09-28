import { useState, useEffect } from 'react';
import { Coin } from '@/types/Coin';

/**
 * Custom React hook for fetching detailed information for a specific cryptocurrency
 * Implements a two-tier caching strategy: first checks local cache, then falls back to API
 * 
 * @param id - The unique identifier of the cryptocurrency to fetch (e.g., "bitcoin")
 * @param coinsCache - Optional array of pre-loaded coins for immediate cache lookup
 * @returns Object containing coin data, loading state, and error state
 */
export const useCoin = (id: string | null, coinsCache?: Coin[]) => {
  // State for storing the detailed coin information
  const [coin, setCoin] = useState<Coin | null>(null);
  // State to track loading status during data fetching
  const [loading, setLoading] = useState(true);
  // State to track any errors during the data fetching process
  const [error, setError] = useState('');

  /**
   * useEffect hook handles the data fetching lifecycle
   * - Validates input parameters
   * - Checks cache for immediate data
   * - Fetches from API if cache miss
   * - Manages loading and error states
   */
  useEffect(() => {
    // Validate that a coin ID was provided
    if (!id) {
      setError('No coin ID provided');
      setLoading(false);
      return;
    }

    // =========================================================================
    // CACHE FIRST STRATEGY: Check if coin exists in provided cache
    // =========================================================================
    if (coinsCache) {
      // Search for the coin in the cached coins array
      const cachedCoin = coinsCache.find(c => c.id === id);
      if (cachedCoin) {
        // If found in cache, use it immediately and skip API call
        setCoin(cachedCoin);
        setLoading(false);
        return; // Exit early since we have the data
      }
    }

    /**
     * Fetches detailed coin information from the backend API
     * Only called when coin is not found in cache
     */
    const fetchCoin = async () => {
      try {
        // Make API request to backend for detailed coin data
        const response = await fetch(`http://localhost:8000/crypto/${id}`);
        
        // Check if response was successful (status 200-299)
        if (!response.ok) throw new Error('Failed to fetch coin');

        // Parse JSON response from backend
        const data = await response.json();
        
        // Update state with fetched coin data
        setCoin(data);
        setError(''); // Clear any previous errors
      } catch (err) {
        // Handle any errors during the fetch process
        console.error(err);
        setError('Failed to fetch coin details');
      } finally {
        // Always set loading to false when operation completes
        setLoading(false);
      }
    };

    // Execute the API call since coin wasn't found in cache
    fetchCoin();
  }, [id, coinsCache]); // Re-run effect when id or coinsCache changes

  /**
   * Return the hook's public interface
   * - coin: Detailed coin information or null if not loaded/not found
   * - loading: Boolean indicating if data is currently being fetched
   * - error: String containing any error message, empty string if no error
   */
  return { coin, loading, error };
};