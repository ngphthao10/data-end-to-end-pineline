'use client'

import { useState, useEffect } from 'react'
import axios from 'axios'
import {
  Database, Activity, CheckCircle, XCircle, RefreshCw, Plus, Trash2,
  Edit2, User, Mail, Hash, Clock, ArrowRight, Server, Box
} from 'lucide-react'

const API_BASE_URL = 'http://localhost:5000/api'

interface Customer {
  id: number
  first_name: string
  last_name: string
  email: string
  phone?: string
}

interface CDCEvent {
  op: string
  before: any
  after: any
  timestamp: number
  source: string
}

interface Stats {
  mysql_count: number
  postgres_count: number
  in_sync: boolean
}

export default function Home() {
  const [mysqlCustomers, setMysqlCustomers] = useState<Customer[]>([])
  const [postgresCustomers, setPostgresCustomers] = useState<Customer[]>([])
  const [cdcEvents, setCdcEvents] = useState<CDCEvent[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [connectorStatus, setConnectorStatus] = useState<any>(null)
  const [showAddForm, setShowAddForm] = useState(false)
  const [showEditForm, setShowEditForm] = useState(false)
  const [editingCustomer, setEditingCustomer] = useState<Customer | null>(null)
  const [newCustomer, setNewCustomer] = useState({ id: '', first_name: '', last_name: '', email: '' })
  const [loading, setLoading] = useState(false)

  const fetchData = async () => {
    try {
      const [mysql, postgres, events, statsData, connector] = await Promise.all([
        axios.get(`${API_BASE_URL}/mysql/customers`),
        axios.get(`${API_BASE_URL}/postgres/customers`),
        axios.get(`${API_BASE_URL}/cdc/events`),
        axios.get(`${API_BASE_URL}/stats`),
        axios.get(`${API_BASE_URL}/connector/status`),
      ])

      setMysqlCustomers(mysql.data)
      setPostgresCustomers(postgres.data)
      setCdcEvents(events.data.reverse().slice(0, 20))
      setStats(statsData.data)
      setConnectorStatus(connector.data)
    } catch (error) {
      console.error('Error fetching data:', error)
    }
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 2000)
    return () => clearInterval(interval)
  }, [])

  const handleAddCustomer = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await axios.post(`${API_BASE_URL}/mysql/customers`, newCustomer)
      setNewCustomer({ id: '', first_name: '', last_name: '', email: '' })
      setShowAddForm(false)
      await fetchData()
    } catch (error: any) {
      alert(error.response?.data?.error || 'Failed to add customer')
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateCustomer = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editingCustomer) return
    setLoading(true)
    try {
      await axios.put(`${API_BASE_URL}/mysql/customers/${editingCustomer.id}`, {
        first_name: editingCustomer.first_name,
        last_name: editingCustomer.last_name,
        email: editingCustomer.email
      })
      setShowEditForm(false)
      setEditingCustomer(null)
      await fetchData()
    } catch (error: any) {
      alert(error.response?.data?.error || 'Failed to update customer')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteCustomer = async (id: number) => {
    if (confirm(`Delete customer ID ${id}?`)) {
      try {
        await axios.delete(`${API_BASE_URL}/mysql/customers/${id}`)
        await fetchData()
      } catch (error) {
        alert('Failed to delete customer')
      }
    }
  }

  const openEditForm = (customer: Customer) => {
    setEditingCustomer(customer)
    setShowEditForm(true)
  }

  const getOperationBadge = (op: string) => {
    const configs: Record<string, { label: string; color: string; icon: any }> = {
      'r': { label: 'Snapshot', color: 'bg-blue-100 text-blue-700 border-blue-200', icon: Box },
      'c': { label: 'Create', color: 'bg-green-100 text-green-700 border-green-200', icon: Plus },
      'u': { label: 'Update', color: 'bg-amber-100 text-amber-700 border-amber-200', icon: Edit2 },
      'd': { label: 'Delete', color: 'bg-red-100 text-red-700 border-red-200', icon: Trash2 }
    }
    const config = configs[op] || { label: op, color: 'bg-gray-100 text-gray-700 border-gray-200', icon: Activity }
    const Icon = config.icon
    return (
      <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium border ${config.color}`}>
        <Icon className="w-3 h-3" />
        {config.label}
      </span>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Simple Header */}
      <header className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Activity className="w-8 h-8 text-gray-700" />
              <div>
                <h1 className="text-xl font-semibold text-gray-900">CDC Dashboard</h1>
                <div className="flex items-center gap-2 text-xs text-gray-600 mt-0.5">
                  <Database className="w-3 h-3" />
                  <span>MySQL</span>
                  <ArrowRight className="w-3 h-3" />
                  <Server className="w-3 h-3" />
                  <span>Kafka</span>
                  <ArrowRight className="w-3 h-3" />
                  <Database className="w-3 h-3" />
                  <span>PostgreSQL</span>
                </div>
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
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        {/* Simple Stats */}
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-white border rounded-lg p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-50 rounded-lg">
                <Database className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <div className="text-xs text-gray-600">MySQL</div>
                <div className="text-2xl font-semibold text-gray-900">{stats?.mysql_count || 0}</div>
              </div>
            </div>
          </div>

          <div className="bg-white border rounded-lg p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-50 rounded-lg">
                <Database className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <div className="text-xs text-gray-600">PostgreSQL</div>
                <div className="text-2xl font-semibold text-gray-900">{stats?.postgres_count || 0}</div>
              </div>
            </div>
          </div>

          <div className="bg-white border rounded-lg p-4">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg ${stats?.in_sync ? 'bg-green-50' : 'bg-red-50'}`}>
                {stats?.in_sync ? (
                  <CheckCircle className="w-5 h-5 text-green-600" />
                ) : (
                  <XCircle className="w-5 h-5 text-red-600" />
                )}
              </div>
              <div>
                <div className="text-xs text-gray-600">Status</div>
                <div className={`text-sm font-medium ${stats?.in_sync ? 'text-green-700' : 'text-red-700'}`}>
                  {stats?.in_sync ? 'In Sync' : 'Syncing'}
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white border rounded-lg p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-50 rounded-lg">
                <Server className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <div className="text-xs text-gray-600">Connector</div>
                <div className="text-sm font-medium text-gray-900">
                  {connectorStatus?.connector?.state || 'Unknown'}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Tables */}
        <div className="grid grid-cols-2 gap-6">
          {/* MySQL */}
          <div className="bg-white border rounded-lg overflow-hidden">
            <div className="px-4 py-3 border-b bg-gray-50">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Database className="w-4 h-4 text-gray-600" />
                  <span className="text-sm font-medium text-gray-900">MySQL Source</span>
                  <span className="text-xs text-gray-500">({mysqlCustomers.length})</span>
                </div>
                <button
                  onClick={() => setShowAddForm(true)}
                  className="flex items-center gap-1 px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  <Plus className="w-3 h-3" />
                  Add
                </button>
              </div>
            </div>
            <div className="overflow-auto" style={{ maxHeight: '500px' }}>
              <table className="w-full text-sm">
                <thead className="bg-gray-50 sticky top-0 text-xs">
                  <tr className="border-b">
                    <th className="px-4 py-2 text-left font-medium text-gray-600">
                      <div className="flex items-center gap-1">
                        <Hash className="w-3 h-3" />
                        ID
                      </div>
                    </th>
                    <th className="px-4 py-2 text-left font-medium text-gray-600">
                      <div className="flex items-center gap-1">
                        <User className="w-3 h-3" />
                        Name
                      </div>
                    </th>
                    <th className="px-4 py-2 text-left font-medium text-gray-600">
                      <div className="flex items-center gap-1">
                        <Mail className="w-3 h-3" />
                        Email
                      </div>
                    </th>
                    <th className="px-4 py-2 text-center font-medium text-gray-600">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {mysqlCustomers.map((customer) => (
                    <tr key={customer.id} className="border-b hover:bg-gray-50">
                      <td className="px-4 py-2 font-mono text-xs text-gray-900">{customer.id}</td>
                      <td className="px-4 py-2 text-gray-900">
                        {customer.first_name} {customer.last_name}
                      </td>
                      <td className="px-4 py-2 text-gray-600 text-xs">{customer.email}</td>
                      <td className="px-4 py-2">
                        <div className="flex items-center justify-center gap-1">
                          <button
                            onClick={() => openEditForm(customer)}
                            className="p-1.5 text-blue-600 hover:bg-blue-50 rounded"
                            title="Edit"
                          >
                            <Edit2 className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleDeleteCustomer(customer.id)}
                            className="p-1.5 text-red-600 hover:bg-red-50 rounded"
                            title="Delete"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* PostgreSQL */}
          <div className="bg-white border rounded-lg overflow-hidden">
            <div className="px-4 py-3 border-b bg-gray-50">
              <div className="flex items-center gap-3">
                <Database className="w-4 h-4 text-gray-600" />
                <span className="text-sm font-medium text-gray-900">PostgreSQL Target</span>
                <span className="text-xs text-gray-500">({postgresCustomers.length})</span>
              </div>
            </div>
            <div className="overflow-auto" style={{ maxHeight: '500px' }}>
              <table className="w-full text-sm">
                <thead className="bg-gray-50 sticky top-0 text-xs">
                  <tr className="border-b">
                    <th className="px-4 py-2 text-left font-medium text-gray-600">
                      <div className="flex items-center gap-1">
                        <Hash className="w-3 h-3" />
                        ID
                      </div>
                    </th>
                    <th className="px-4 py-2 text-left font-medium text-gray-600">
                      <div className="flex items-center gap-1">
                        <User className="w-3 h-3" />
                        Name
                      </div>
                    </th>
                    <th className="px-4 py-2 text-left font-medium text-gray-600">
                      <div className="flex items-center gap-1">
                        <Mail className="w-3 h-3" />
                        Email
                      </div>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {postgresCustomers.map((customer) => (
                    <tr key={customer.id} className="border-b hover:bg-gray-50">
                      <td className="px-4 py-3 font-mono text-xs text-gray-900">{customer.id}</td>
                      <td className="px-4 py-3 text-gray-900">
                        {customer.first_name} {customer.last_name}
                      </td>
                      <td className="px-4 py-3 text-gray-600 text-xs">{customer.email}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* CDC Events */}
        <div className="bg-white border rounded-lg">
          <div className="px-4 py-3 border-b bg-gray-50">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-gray-600" />
              <span className="text-sm font-medium text-gray-900">CDC Events</span>
              <span className="text-xs text-gray-500">({cdcEvents.length} recent)</span>
            </div>
          </div>
          <div className="p-4">
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {cdcEvents.length === 0 ? (
                <div className="text-center py-8 text-gray-500 text-sm">
                  <Activity className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                  No recent events
                </div>
              ) : (
                cdcEvents.map((event, index) => (
                  <div key={index} className="border rounded-lg p-3 hover:bg-gray-50">
                    <div className="flex items-center justify-between mb-2">
                      {getOperationBadge(event.op)}
                      <div className="flex items-center gap-1 text-xs text-gray-500">
                        <Clock className="w-3 h-3" />
                        {new Date(event.timestamp).toLocaleString()}
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      {event.before && (
                        <div className="text-sm">
                          <div className="text-xs text-gray-500 mb-1 flex items-center gap-1">
                            <ArrowRight className="w-3 h-3" />
                            Before
                          </div>
                          <div className="font-medium text-gray-900">
                            {event.before.first_name} {event.before.last_name}
                          </div>
                          <div className="text-xs text-gray-600">{event.before.email}</div>
                        </div>
                      )}
                      {event.after && (
                        <div className="text-sm">
                          <div className="text-xs text-gray-500 mb-1 flex items-center gap-1">
                            <ArrowRight className="w-3 h-3" />
                            After
                          </div>
                          <div className="font-medium text-gray-900">
                            {event.after.first_name} {event.after.last_name}
                          </div>
                          <div className="text-xs text-gray-600">{event.after.email}</div>
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </main>

      {/* Add Modal */}
      {showAddForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg w-full max-w-md">
            <div className="px-4 py-3 border-b flex items-center gap-2">
              <Plus className="w-5 h-5 text-gray-700" />
              <h3 className="text-lg font-medium">Add Customer</h3>
            </div>
            <form onSubmit={handleAddCustomer} className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
                  <Hash className="w-4 h-4" />
                  ID
                </label>
                <input
                  type="number"
                  required
                  value={newCustomer.id}
                  onChange={(e) => setNewCustomer({ ...newCustomer, id: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
                  <User className="w-4 h-4" />
                  First Name
                </label>
                <input
                  type="text"
                  required
                  value={newCustomer.first_name}
                  onChange={(e) => setNewCustomer({ ...newCustomer, first_name: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
                  <User className="w-4 h-4" />
                  Last Name
                </label>
                <input
                  type="text"
                  required
                  value={newCustomer.last_name}
                  onChange={(e) => setNewCustomer({ ...newCustomer, last_name: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
                  <Mail className="w-4 h-4" />
                  Email
                </label>
                <input
                  type="email"
                  required
                  value={newCustomer.email}
                  onChange={(e) => setNewCustomer({ ...newCustomer, email: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex gap-2 pt-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? 'Adding...' : 'Add'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowAddForm(false)}
                  className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditForm && editingCustomer && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg w-full max-w-md">
            <div className="px-4 py-3 border-b flex items-center gap-2">
              <Edit2 className="w-5 h-5 text-gray-700" />
              <h3 className="text-lg font-medium">Edit Customer</h3>
            </div>
            <form onSubmit={handleUpdateCustomer} className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
                  <Hash className="w-4 h-4" />
                  ID
                </label>
                <input
                  type="number"
                  disabled
                  value={editingCustomer.id}
                  className="w-full px-3 py-2 border rounded-lg text-sm bg-gray-50 text-gray-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
                  <User className="w-4 h-4" />
                  First Name
                </label>
                <input
                  type="text"
                  required
                  value={editingCustomer.first_name}
                  onChange={(e) => setEditingCustomer({ ...editingCustomer, first_name: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
                  <User className="w-4 h-4" />
                  Last Name
                </label>
                <input
                  type="text"
                  required
                  value={editingCustomer.last_name}
                  onChange={(e) => setEditingCustomer({ ...editingCustomer, last_name: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
                  <Mail className="w-4 h-4" />
                  Email
                </label>
                <input
                  type="email"
                  required
                  value={editingCustomer.email}
                  onChange={(e) => setEditingCustomer({ ...editingCustomer, email: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex gap-2 pt-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? 'Updating...' : 'Update'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowEditForm(false)
                    setEditingCustomer(null)
                  }}
                  className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
