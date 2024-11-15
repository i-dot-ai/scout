// components/Footer.tsx
import React, { useEffect, useRef } from 'react';
import { Link } from '@mui/material';

const Footer: React.FC = () => {
  const footerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleScroll = () => {
      if (footerRef.current) {
        const windowHeight = window.innerHeight;
        const documentHeight = document.documentElement.scrollHeight;
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollBottom = scrollTop + windowHeight;

        if (scrollBottom >= documentHeight - 10) {
          footerRef.current.classList.add('visible');
        } else {
          footerRef.current.classList.remove('visible');
        }
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <footer ref={footerRef} className="App-footer">
      <div className="footer-content">
        <Link href="/privacy-policy" className="footer-link">Privacy Policy</Link>
        <a href="mailto:support@example.com" className="footer-link">Contact Support</a>
      </div>
    </footer>
  );
};

export default Footer;
