'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { BarChart3, Search, Grid3X3, TrendingUp } from 'lucide-react'

const navItems = [
  { href: '/', label: 'Home', icon: BarChart3 },
  { href: '/brands', label: 'Brands', icon: Search },
  { href: '/categories', label: 'Categories', icon: Grid3X3 },
  { href: '/rankings', label: 'Rankings', icon: TrendingUp },
]

export function Navigation() {
  const pathname = usePathname()

  return (
    <nav className="bg-white border-b sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link href="/" className="font-semibold text-lg text-gray-900">
            Brand Partisan Lean
          </Link>
          <div className="flex items-center space-x-1">
            {navItems.map(({ href, label, icon: Icon }) => {
              const isActive = pathname === href || (href !== '/' && pathname.startsWith(href))
              return (
                <Link
                  key={href}
                  href={href}
                  className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-gray-100 text-gray-900'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {label}
                </Link>
              )
            })}
          </div>
        </div>
      </div>
    </nav>
  )
}
