import type { Metadata, Viewport } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
  weight: ['300', '400', '500', '600', '700', '800'],
});

export const metadata: Metadata = {
  title: {
    default: 'Hackathon Eval Engine',
    template: '%s | Hackathon Eval Engine',
  },
  description: 'AI-powered hackathon evaluation platform with multi-agent scoring, real-time feedback, and intelligent mentorship.',
  keywords: ['hackathon', 'evaluation', 'AI', 'code review', 'scoring'],
};

export const viewport: Viewport = {
  themeColor: '#0a0a0a',
  colorScheme: 'dark',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} dark`}>
      <body className={`${inter.className} bg-[#13141a] text-gray-100 antialiased min-h-screen`}>
        {children}
      </body>
    </html>
  );
}
