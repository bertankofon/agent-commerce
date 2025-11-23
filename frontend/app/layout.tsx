'use client';
import type { Metadata } from "next";
import "./globals.css";
import { PrivyProvider } from '@privy-io/react-auth';
import { privyConfig } from './lib/privy-config';

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <PrivyProvider
          appId={process.env.NEXT_PUBLIC_PRIVY_APP_ID || ''}
          config={privyConfig}
        >
          {children}
        </PrivyProvider>
      </body>
    </html>
  );
}
