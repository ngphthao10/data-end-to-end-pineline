'use client'

import { useState, useEffect } from 'react'
import axios from 'axios'
import { History, User, Package, Search, ArrowRight, Clock } from 'lucide-react'

interface HistoryRecord {
  customer_key?: number
  product_key?: number
  customer_id?: number
  product_id?: number
  first_name?: string
  last_name?: string
  product_name?: string
  email?: string
  phone?: string
  address?: string
  city?: string
  country?: string
  category?: string
  brand?: string
  price?: number
  cost?: number
  valid_from: string
  valid_to: string
  is_current: boolean
  version: number
}

export default function SCDHistory() {
  const [entityType, setEntityType] = useState<'customer' | 'product'>('customer')
  const [entityId, setEntityId] = useState('')
  const [history, setHistory] = useState<HistoryRecord[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)

  const fetchHistory = async () => {
    if (!entityId) return

    setLoading(true)
    setSearched(true)
    try {
      const endpoint = entityType === 'customer'
        ? `/api/customers/${entityId}/history`
        : `/api/products/${entityId}/history`

      const response = await axios.get(`http://localhost:5000${endpoint}`)
      setHistory(response.data.data || [])
    } catch (error) {
      console.error('Error fetching history:', error)
      setHistory([])
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    fetchHistory()
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="px-6 py-4">
          <h1 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
            <History className="w-5 h-5" />
            SCD History
          </h1>
          <p className="text-sm text-gray-500 mt-1">View historical changes tracked by SCD Type 2</p>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Search Form */}
        <div className="bg-white border rounded-lg p-4">
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              {/* Entity Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Entity Type
                </label>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setEntityType('customer')}
                    className={`flex-1 px-4 py-2 text-sm rounded-lg border transition-colors ${
                      entityType === 'customer'
                        ? 'bg-blue-50 border-blue-200 text-blue-700 font-medium'
                        : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <User className="w-4 h-4 inline mr-2" />
                    Customer
                  </button>
                  <button
                    type="button"
                    onClick={() => setEntityType('product')}
                    className={`flex-1 px-4 py-2 text-sm rounded-lg border transition-colors ${
                      entityType === 'product'
                        ? 'bg-green-50 border-green-200 text-green-700 font-medium'
                        : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <Package className="w-4 h-4 inline mr-2" />
                    Product
                  </button>
                </div>
              </div>

              {/* Entity ID */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {entityType === 'customer' ? 'Customer ID' : 'Product ID'}
                </label>
                <input
                  type="number"
                  value={entityId}
                  onChange={(e) => setEntityId(e.target.value)}
                  placeholder={`Enter ${entityType} ID...`}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Search Button */}
              <div className="flex items-end">
                <button
                  type="submit"
                  disabled={!entityId || loading}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Search className="w-4 h-4" />
                  {loading ? 'Searching...' : 'Search History'}
                </button>
              </div>
            </div>
          </form>
        </div>

        {/* History Results */}
        {searched && (
          <div className="bg-white border rounded-lg">
            <div className="px-4 py-3 border-b bg-gray-50">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-900">
                  History for {entityType === 'customer' ? 'Customer' : 'Product'} #{entityId}
                </span>
                <span className="text-xs text-gray-500">{history.length} versions found</span>
              </div>
            </div>
            <div className="p-4">
              {history.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <History className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                  <p className="text-sm">No history found for this {entityType}</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {history.map((record, index) => (
                    <div
                      key={index}
                      className={`border rounded-lg p-4 ${
                        record.is_current ? 'bg-green-50 border-green-200' : 'bg-white'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center text-sm font-medium text-gray-700">
                            v{record.version}
                          </div>
                          {record.is_current && (
                            <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded border border-green-200">
                              Current
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-2 text-xs text-gray-500">
                          <Clock className="w-3 h-3" />
                          <span>{new Date(record.valid_from).toLocaleString()}</span>
                          <ArrowRight className="w-3 h-3" />
                          <span>
                            {record.valid_to === '9999-12-31' || record.valid_to === '9999-12-31T00:00:00'
                              ? 'Present'
                              : new Date(record.valid_to).toLocaleString()}
                          </span>
                        </div>
                      </div>

                      {/* Customer Details */}
                      {entityType === 'customer' && (
                        <div className="grid grid-cols-3 gap-4 text-sm">
                          <div>
                            <div className="text-xs text-gray-500 mb-1">Name</div>
                            <div className="font-medium text-gray-900">
                              {record.first_name} {record.last_name}
                            </div>
                          </div>
                          <div>
                            <div className="text-xs text-gray-500 mb-1">Email</div>
                            <div className="text-gray-700">{record.email}</div>
                          </div>
                          <div>
                            <div className="text-xs text-gray-500 mb-1">Phone</div>
                            <div className="text-gray-700">{record.phone || 'N/A'}</div>
                          </div>
                          <div>
                            <div className="text-xs text-gray-500 mb-1">Address</div>
                            <div className="text-gray-700">{record.address || 'N/A'}</div>
                          </div>
                          <div>
                            <div className="text-xs text-gray-500 mb-1">City</div>
                            <div className="text-gray-700">{record.city || 'N/A'}</div>
                          </div>
                          <div>
                            <div className="text-xs text-gray-500 mb-1">Country</div>
                            <div className="text-gray-700">{record.country || 'N/A'}</div>
                          </div>
                        </div>
                      )}

                      {/* Product Details */}
                      {entityType === 'product' && (
                        <div className="grid grid-cols-4 gap-4 text-sm">
                          <div>
                            <div className="text-xs text-gray-500 mb-1">Product Name</div>
                            <div className="font-medium text-gray-900">{record.product_name}</div>
                          </div>
                          <div>
                            <div className="text-xs text-gray-500 mb-1">Category</div>
                            <div className="text-gray-700">{record.category}</div>
                          </div>
                          <div>
                            <div className="text-xs text-gray-500 mb-1">Brand</div>
                            <div className="text-gray-700">{record.brand || 'N/A'}</div>
                          </div>
                          <div>
                            <div className="text-xs text-gray-500 mb-1">Price</div>
                            <div className="font-medium text-gray-900">
                              ${record.price?.toFixed(2) || '0.00'}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Info Box */}
        {!searched && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <History className="w-5 h-5 text-blue-600 mt-0.5" />
              <div className="text-sm text-blue-900">
                <div className="font-medium mb-1">About SCD Type 2 History</div>
                <p className="text-blue-700">
                  SCD (Slowly Changing Dimension) Type 2 tracks historical changes by creating new versions
                  of records. Each version has a validity period showing when it was active. This allows you
                  to see exactly what data looked like at any point in time.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
