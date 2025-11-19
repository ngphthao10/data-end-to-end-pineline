'use client'

import { useState, useEffect } from 'react'
import axios from 'axios'
import {
  Database, Activity, CheckCircle, XCircle, RefreshCw, Clock,
  ArrowRight, User, Mail, Hash, Package, DollarSign
} from 'lucide-react'

interface Stats {
  source: {
    customers: number
    products: number
    orders: number
  }
  warehouse: {
    customers: number
    products: number
    orders: number
  }
  sync_percentages: {
    customers: number
    products: number
    orders: number
  }
  in_sync: boolean
}

interface CDCEvent {
  entity_type: string
  entity_id: number
  entity_name: string
  email?: string
  price?: number
  change_time: string
  version: number
  is_current: boolean
  change_type: string
}

export default function CDCMonitoring() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [events, setEvents] = useState<CDCEvent[]>([])
  const [loading, setLoading] = useState(true)

  const fetchData = async () => {
    try {
      const [statsRes, eventsRes] = await Promise.all([
        axios.get('http://localhost:5000/api/cdc/stats'),
        axios.get('http://localhost:5000/api/cdc/recent-changes?limit=20'),
      ])

      setStats(statsRes.data.data)
      setEvents(eventsRes.data.data || [])
    } catch (error) {
      console.error('Error fetching data:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 2000)
    return () => clearInterval(interval)
  }, [])

  const getChangeBadge = (changeType: string) => {
    const configs: Record<string, { label: string; color: string }> = {
      'create': { label: 'Create', color: 'bg-green-100 text-green-700 border-green-200' },
      'update': { label: 'Update', color: 'bg-amber-100 text-amber-700 border-amber-200' },
      'current': { label: 'Current', color: 'bg-blue-100 text-blue-700 border-blue-200' },
    }
    const config = configs[changeType] || { label: changeType, color: 'bg-gray-100 text-gray-700 border-gray-200' }
    return (
      <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium border ${config.color}`}>
        {config.label}
      </span>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                <Activity className="w-5 h-5" />
                CDC Monitoring
              </h1>
              <div className="flex items-center gap-2 text-xs text-gray-600 mt-1">
                <Database className="w-3 h-3" />
                <span>PostgreSQL Source</span>
                <ArrowRight className="w-3 h-3" />
                <Activity className="w-3 h-3" />
                <span>Kafka</span>
                <ArrowRight className="w-3 h-3" />
                <Database className="w-3 h-3" />
                <span>PostgreSQL Warehouse</span>
              </div>
            </div>
            <button
              onClick={fetchData}
              className="flex items-center gap-2 px-4 py-2 text-sm bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Sync Status Cards */}
        <div className="grid grid-cols-3 gap-4">
          {/* Source Stats */}
          <div className="bg-white border rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <Database className="w-4 h-4 text-gray-600" />
              <span className="text-sm font-medium text-gray-900">Source Database</span>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Customers</span>
                <span className="font-medium text-gray-900">{stats?.source.customers.toLocaleString()}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Products</span>
                <span className="font-medium text-gray-900">{stats?.source.products.toLocaleString()}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Orders</span>
                <span className="font-medium text-gray-900">{stats?.source.orders.toLocaleString()}</span>
              </div>
            </div>
          </div>

          {/* Sync Status */}
          <div className="bg-white border rounded-lg p-4 flex items-center justify-center">
            <div className="text-center">
              {stats?.in_sync ? (
                <>
                  <CheckCircle className="w-12 h-12 text-green-600 mx-auto mb-2" />
                  <div className="text-sm font-medium text-green-700">In Sync</div>
                  <div className="text-xs text-gray-500 mt-1">All data synchronized</div>
                </>
              ) : (
                <>
                  <Activity className="w-12 h-12 text-amber-600 mx-auto mb-2 animate-pulse" />
                  <div className="text-sm font-medium text-amber-700">Syncing</div>
                  <div className="text-xs text-gray-500 mt-1">Processing changes...</div>
                </>
              )}
            </div>
          </div>

          {/* Warehouse Stats */}
          <div className="bg-white border rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <Database className="w-4 h-4 text-gray-600" />
              <span className="text-sm font-medium text-gray-900">Warehouse Database</span>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Customers</span>
                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-900">{stats?.warehouse.customers.toLocaleString()}</span>
                  {stats?.sync_percentages && (
                    <span className={`text-xs px-1.5 py-0.5 rounded ${
                      stats.sync_percentages.customers === 100
                        ? 'bg-green-100 text-green-700'
                        : 'bg-amber-100 text-amber-700'
                    }`}>
                      {stats.sync_percentages.customers.toFixed(0)}%
                    </span>
                  )}
                </div>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Products</span>
                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-900">{stats?.warehouse.products.toLocaleString()}</span>
                  {stats?.sync_percentages && (
                    <span className={`text-xs px-1.5 py-0.5 rounded ${
                      stats.sync_percentages.products === 100
                        ? 'bg-green-100 text-green-700'
                        : 'bg-amber-100 text-amber-700'
                    }`}>
                      {stats.sync_percentages.products.toFixed(0)}%
                    </span>
                  )}
                </div>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Orders</span>
                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-900">{stats?.warehouse.orders.toLocaleString()}</span>
                  {stats?.sync_percentages && (
                    <span className={`text-xs px-1.5 py-0.5 rounded ${
                      stats.sync_percentages.orders >= 95
                        ? 'bg-green-100 text-green-700'
                        : stats.sync_percentages.orders >= 80
                        ? 'bg-amber-100 text-amber-700'
                        : 'bg-red-100 text-red-700'
                    }`}>
                      {stats.sync_percentages.orders.toFixed(0)}%
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* CDC Events */}
        <div className="bg-white border rounded-lg">
          <div className="px-4 py-3 border-b bg-gray-50">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-gray-600" />
              <span className="text-sm font-medium text-gray-900">Recent CDC Events</span>
              <span className="text-xs text-gray-500">({events.length})</span>
            </div>
          </div>
          <div className="p-4">
            <div className="space-y-3 max-h-[600px] overflow-y-auto">
              {events.length === 0 ? (
                <div className="text-center py-8 text-gray-500 text-sm">
                  <Activity className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                  No recent events
                </div>
              ) : (
                events.map((event, index) => (
                  <div key={index} className="border rounded-lg p-3 hover:bg-gray-50">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {event.entity_type === 'customer' ? (
                          <User className="w-4 h-4 text-blue-600" />
                        ) : (
                          <Package className="w-4 h-4 text-green-600" />
                        )}
                        <span className="text-xs font-medium text-gray-500 uppercase">
                          {event.entity_type}
                        </span>
                        {getChangeBadge(event.change_type)}
                      </div>
                      <div className="flex items-center gap-1 text-xs text-gray-500">
                        <Clock className="w-3 h-3" />
                        {new Date(event.change_time).toLocaleString()}
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-3 ml-6">
                      <div>
                        <div className="text-xs text-gray-500 mb-1 flex items-center gap-1">
                          <Hash className="w-3 h-3" />
                          ID: {event.entity_id}
                        </div>
                        <div className="font-medium text-sm text-gray-900">{event.entity_name}</div>
                      </div>
                      <div>
                        {event.entity_type === 'customer' && event.email && (
                          <div className="text-xs">
                            <div className="text-gray-500 mb-1 flex items-center gap-1">
                              <Mail className="w-3 h-3" />
                              Email
                            </div>
                            <div className="text-gray-700">{event.email}</div>
                          </div>
                        )}
                        {event.entity_type === 'product' && event.price !== undefined && (
                          <div className="text-xs">
                            <div className="text-gray-500 mb-1 flex items-center gap-1">
                              <DollarSign className="w-3 h-3" />
                              Price
                            </div>
                            <div className="text-gray-700 font-medium">${event.price.toFixed(2)}</div>
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-3 mt-2 ml-6 text-xs text-gray-500">
                      <span>Version: {event.version}</span>
                      {event.is_current && (
                        <span className="flex items-center gap-1 text-green-600">
                          <CheckCircle className="w-3 h-3" />
                          Current
                        </span>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
