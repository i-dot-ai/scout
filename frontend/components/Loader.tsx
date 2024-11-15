import React from 'react';

// Import the GIF directly in the component
import loadingGif from '@/public/assets/magnifying-glass.gif';
import Image from 'next/image';
interface MagnifyingGlassLoaderProps {
  size?: number;
}

const MagnifyingGlassLoader: React.FC<MagnifyingGlassLoaderProps> = ({ size = 80 }) => {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100%',
      width: '100%'
    }}>
      <Image
        src={loadingGif}
        alt="Loading..."
        width={size}
        height={size}
        style={{ objectFit: 'contain' }}
      />
    </div>
  );
};

export default MagnifyingGlassLoader;
