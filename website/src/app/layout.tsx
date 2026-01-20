import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Navigation } from '@/components/Navigation'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Brand Partisan Lean Explorer',
  description: 'Explore the partisan composition of brand customer bases using foot traffic data',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Navigation />
        <main className="min-h-screen bg-gray-50">
          {children}
        </main>
        <footer className="bg-white border-t py-8">
          <div className="max-w-7xl mx-auto px-4 text-center text-sm text-gray-500">
            <p>Brand Partisan Lean Explorer</p>
            <p className="mt-1">Research project - UC Berkeley</p>
            <p className="mt-2">
              <a href="mailto:maxkagan@berkeley.edu" className="text-blue-600 hover:underline">
                Contact for data access
              </a>
            </p>
          </div>
        </footer>
      </body>
    </html>
  )
}
