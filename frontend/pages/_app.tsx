import type { AppProps } from 'next/app'
import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import '../public/styles/App.css';
import '../public/styles/index.css';
import '../public/styles/FileViewer.css';

export default function MyApp({ Component, pageProps }: AppProps) {
    const router = useRouter();

    const isActive = (pathname: string) => router.pathname === pathname;

    return (
        <div className="App">
            <header className="App-header">
                <div className="header-content">
                    <h1>🔎 IPA Scout</h1>
                    <nav className="header-nav">
                        <Link href="/" passHref legacyBehavior>
                            <a className={`nav-link ${isActive('/') ? 'active' : ''}`}>Summary</a>
                        </Link>
                        <Link href="/results" passHref legacyBehavior>
                            <a className={`nav-link ${isActive('/results') ? 'active' : ''}`}>Results</a>
                        </Link>
                        <Link href="/file-viewer/" passHref legacyBehavior>
                            <a className={`nav-link ${isActive('/file-viewer') ? 'active' : ''}`}>File Viewer</a>
                        </Link>
                    </nav>
                </div>
            </header>
            <main className="main-content">
                <Component {...pageProps} />
            </main>
            <footer className="App-footer">
                <div className="footer-content">
                    <Link href="/privacy-policy" passHref legacyBehavior>
                        <a>Privacy Policy</a>
                    </Link>
                    <span className="footer-separator">|</span>
                    <a href="mailto:i-dot-ai-enquiries@cabinetoffice.gov.uk">Support</a>
                </div>
            </footer>
        </div>
    );
};
