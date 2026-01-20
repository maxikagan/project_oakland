'use client'

import { useState, useEffect, useMemo } from 'react'
import Link from 'next/link'
import { Search, SortAsc, SortDesc } from 'lucide-react'
import { Brand } from '@/types'
import { LeanIndicator, LeanBadge } from '@/components/LeanIndicator'

type SortField = 'name' | 'lean_2020' | 'total_visits'
type SortDirection = 'asc' | 'desc'

export default function BrandsPage() {
  const [brands, setBrands] = useState<Brand[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [sortField, setSortField] = useState<SortField>('total_visits')
  const [sortDir, setSortDir] = useState<SortDirection>('desc')
  const [categoryFilter, setCategoryFilter] = useState<string>('')

  useEffect(() => {
    fetch('/data/brands.json')
      .then(res => res.json())
      .then(data => {
        setBrands(data.brands)
        setLoading(false)
      })
  }, [])

  const categories = useMemo(() => {
    const cats = new Set(brands.map(b => b.category).filter(Boolean))
    return Array.from(cats).sort()
  }, [brands])

  const filteredBrands = useMemo(() => {
    let result = [...brands]

    if (search) {
      const q = search.toLowerCase()
      result = result.filter(b =>
        b.name.toLowerCase().includes(q) ||
        b.company?.toLowerCase().includes(q)
      )
    }

    if (categoryFilter) {
      result = result.filter(b => b.category === categoryFilter)
    }

    result.sort((a, b) => {
      let aVal: number | string | null = a[sortField]
      let bVal: number | string | null = b[sortField]

      if (aVal === null) aVal = sortDir === 'asc' ? Infinity : -Infinity
      if (bVal === null) bVal = sortDir === 'asc' ? Infinity : -Infinity

      if (typeof aVal === 'string') {
        return sortDir === 'asc'
          ? aVal.localeCompare(bVal as string)
          : (bVal as string).localeCompare(aVal)
      }

      return sortDir === 'asc' ? (aVal as number) - (bVal as number) : (bVal as number) - (aVal as number)
    })

    return result
  }, [brands, search, categoryFilter, sortField, sortDir])

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDir(field === 'name' ? 'asc' : 'desc')
    }
  }

  if (loading) {
    return (
      <div className="py-12 text-center">
        <p className="text-gray-500">Loading brands...</p>
      </div>
    )
  }

  return (
    <div className="py-8">
      <div className="max-w-7xl mx-auto px-4">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">All Brands</h1>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search brands..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <select
            value={categoryFilter}
            onChange={e => setCategoryFilter(e.target.value)}
            className="px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All categories</option>
            {categories.map(cat => (
              <option key={cat} value={cat!}>{cat}</option>
            ))}
          </select>
        </div>

        <p className="text-sm text-gray-500 mb-4">
          Showing {filteredBrands.length.toLocaleString()} brands
        </p>

        {/* Table */}
        <div className="bg-white rounded-lg shadow-sm border overflow-hidden overflow-x-auto">
          <table className="w-full divide-y divide-gray-200 table-fixed">
            <thead className="bg-gray-50">
              <tr>
                <th
                  className="w-1/3 px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => toggleSort('name')}
                >
                  <div className="flex items-center gap-1">
                    Brand
                    {sortField === 'name' && (sortDir === 'asc' ? <SortAsc className="w-3 h-3" /> : <SortDesc className="w-3 h-3" />)}
                  </div>
                </th>
                <th className="w-1/4 px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Category
                </th>
                <th
                  className="w-1/4 px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => toggleSort('lean_2020')}
                >
                  <div className="flex items-center gap-1">
                    Partisan Lean
                    {sortField === 'lean_2020' && (sortDir === 'asc' ? <SortAsc className="w-3 h-3" /> : <SortDesc className="w-3 h-3" />)}
                  </div>
                </th>
                <th
                  className="w-1/6 px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => toggleSort('total_visits')}
                >
                  <div className="flex items-center gap-1">
                    Total Visits
                    {sortField === 'total_visits' && (sortDir === 'asc' ? <SortAsc className="w-3 h-3" /> : <SortDesc className="w-3 h-3" />)}
                  </div>
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredBrands.slice(0, 100).map(brand => (
                <tr key={brand.slug} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <Link href={`/brands/${brand.slug}`} className="text-blue-600 hover:text-blue-800 font-medium block truncate">
                      {brand.name}
                    </Link>
                    {brand.ticker && brand.company && brand.company !== brand.name && (
                      <p className="text-xs text-gray-400 truncate">{brand.company}</p>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500 truncate">
                    {brand.category || '-'}
                  </td>
                  <td className="px-6 py-4">
                    <LeanIndicator lean={brand.lean_2020} size="sm" />
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {brand.total_visits.toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {filteredBrands.length > 100 && (
            <div className="px-6 py-3 bg-gray-50 text-sm text-gray-500 text-center">
              Showing first 100 of {filteredBrands.length.toLocaleString()} results. Use search to narrow down.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
