// src/utils/getGateUrl.ts
export const getGateUrl = async (gate: string): Promise<string | null> => {
  try {
    const response = await fetch('/gate_urls.json');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    return data[gate] || null;
  } catch (error) {
    console.error('Error fetching gate URL:', error);
    return null;
  }
};
