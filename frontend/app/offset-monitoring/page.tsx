'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  RefreshCw,
  ArrowLeft,
  Clock,
  Database,
  GitBranch,
  RotateCcw
} from 'lucide-react'

interface KafkaOffset {
  topic: string
  partition: number
  current_offset?: number
  log_end_offset?: number
  lag: number
  consumer_id?: string | null
  failed_count?: number
  min_offset?: number
  max_offset?: number
}

interface FailedMessage {
  id: number
  topic: string
  partition: number
  offset: number
  timestamp: string | null
  error_type: string
  error_message: string
  retry_count: number
  max_retries: number
  status: string
  failed_at: string
  last_retry_at: string | null
  next_retry_at: string | null
}

interface StatusCounts {
  pending?: number
  dead_letter?: number
  resolved?: number
  retrying?: number
}

export default function OffsetMonitoring() {
  const router = useRouter()
  const [offsets, setOffsets] = useState<KafkaOffset[]>([])
  const [failedMessages, setFailedMessages] = useState<FailedMessage[]>([])
  const [statusCounts, setStatusCounts] = useState<StatusCounts>({})
  const [loading, setLoading] = useState(true)
  const [retrying, setRetrying] = useState(false)
  const [selectedStatus, setSelectedStatus] = useState<string>('all')
  const [autoRefresh, setAutoRefresh] = useState(true)

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'

  const fetchData = async () => {
    try {
      const [offsetsRes, summaryRes, messagesRes] = await Promise.all([
        fetch(`${API_URL}/api/monitoring/kafka-offsets`),
        fetch(`${API_URL}/api/monitoring/failed-messages/summary`),
        fetch(`${API_URL}/api/monitoring/failed-messages${selectedStatus === 'all' ? '' : `?status=${selectedStatus}`}`)
      ])

      if (offsetsRes.ok) {
        const data = await offsetsRes.json()
        if (data.success) setOffsets(data.data)
      }

      if (summaryRes.ok) {
        const data = await summaryRes.json()
        if (data.success) setStatusCounts(data.status_counts || {})
      }

      if (messagesRes.ok) {
        const data = await messagesRes.json()
        if (data.success) setFailedMessages(data.data)
      }

      setLoading(false)
    } catch (error) {
      console.error('Error fetching data:', error)
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    if (autoRefresh) {
      const interval = setInterval(fetchData, 10000)
      return () => clearInterval(interval)
    }
  }, [autoRefresh, selectedStatus])

  const retryMessage = async (messageId: number) => {
    if (!confirm(`Retry message #${messageId}?`)) return

    setRetrying(true)
    try {
      const res = await fetch(`${API_URL}/api/monitoring/failed-messages/${messageId}/retry`, {
        method: 'POST'
      })
      const data = await res.json()

      if (data.success) {
        alert('Message retried successfully!')
        fetchData()
      } else {
        alert(`Retry failed: ${data.error}`)
      }
    } catch (error) {
      alert(`Retry failed: ${error}`)
    } finally {
      setRetrying(false)
    }
  }

  const retryAll = async () => {
    if (!confirm('Retry all pending failed messages? This may take a while.')) return

    setRetrying(true)
    try {
      const res = await fetch(`${API_URL}/api/monitoring/failed-messages/retry-all`, {
        method: 'POST'
      })
      const data = await res.json()

      if (data.success) {
        alert('All messages retried successfully!')
        fetchData()
      } else {
        alert(`Retry failed: ${data.error}`)
      }
    } catch (error) {
      alert(`Retry failed: ${error}`)
    } finally {
      setRetrying(false)
    }
  }

  const getLagColor = (lag: number) => {
    if (lag === 0) return 'text-green-600'
    if (lag < 100) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getStatusBadge = (status: string) => {
    const badges: Record<string, { bg: string; text: string }> = {
      pending: { bg: 'bg-yellow-50', text: 'text-yellow-700' },
      retrying: { bg: 'bg-blue-50', text: 'text-blue-700' },
      resolved: { bg: 'bg-green-50', text: 'text-green-700' },
      dead_letter: { bg: 'bg-red-50', text: 'text-red-700' },
      ignored: { bg: 'bg-gray-50', text: 'text-gray-700' }
    }
    return badges[status] || badges.ignored
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  const totalLag = offsets.reduce((sum, o) => sum + o.lag, 0)
  const totalPending = statusCounts.pending || 0
  const totalDeadLetters = statusCounts.dead_letter || 0
  const totalResolved = statusCounts.resolved || 0

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header - Same style as Dashboard */}
      <div className="bg-white border-b">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <button
                onClick={() => router.push('/')}
                className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 mb-2"
              >
                <ArrowLeft className="w-4 h-4" />
                Back to Dashboard
              </button>
              <h1 className="text-xl font-semibold text-gray-900">Offset & Error Monitoring</h1>
              <p className="text-sm text-gray-500 mt-1">Real-time Kafka offset tracking and failed message management</p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`flex items-center gap-2 px-4 py-2 text-sm rounded-lg border ${
                  autoRefresh
                    ? 'bg-green-50 border-green-200 text-green-700'
                    : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                }`}
              >
                <Clock className="w-4 h-4" />
                {autoRefresh ? 'Auto-refresh: ON' : 'Auto-refresh: OFF'}
              </button>
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
      </div>

      <div className="p-6 space-y-6">
        {/* Stats Cards - Same style as Dashboard */}
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-white border rounded-lg p-4">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg ${totalLag === 0 ? 'bg-green-50' : 'bg-yellow-50'}`}>
                <Activity className={`w-5 h-5 ${totalLag === 0 ? 'text-green-600' : 'text-yellow-600'}`} />
              </div>
              <div>
                <div className="text-xs text-gray-600">Total Lag</div>
                <div className={`text-2xl font-semibold ${getLagColor(totalLag)}`}>{totalLag}</div>
              </div>
            </div>
          </div>

          <div className="bg-white border rounded-lg p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-50 rounded-lg">
                <AlertTriangle className="w-5 h-5 text-yellow-600" />
              </div>
              <div>
                <div className="text-xs text-gray-600">Failed Messages</div>
                <div className="text-2xl font-semibold text-gray-900">{totalPending}</div>
              </div>
            </div>
          </div>

          <div className="bg-white border rounded-lg p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-50 rounded-lg">
                <XCircle className="w-5 h-5 text-red-600" />
              </div>
              <div>
                <div className="text-xs text-gray-600">Dead Letters</div>
                <div className="text-2xl font-semibold text-gray-900">{totalDeadLetters}</div>
              </div>
            </div>
          </div>

          <div className="bg-white border rounded-lg p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-50 rounded-lg">
                <CheckCircle2 className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <div className="text-xs text-gray-600">Resolved</div>
                <div className="text-2xl font-semibold text-gray-900">{totalResolved}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Kafka Offsets Section */}
        <div className="bg-white border rounded-lg">
          <div className="px-4 py-3 border-b bg-gray-50">
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-gray-600" />
              <h2 className="text-sm font-medium text-gray-900">Kafka Consumer Offsets</h2>
            </div>
          </div>
          <div className="p-4">
            <div className="space-y-3">
              {offsets.map((offset, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${offset.lag === 0 ? 'bg-green-100' : 'bg-yellow-100'}`}>
                      <GitBranch className={`w-4 h-4 ${offset.lag === 0 ? 'text-green-600' : 'text-yellow-600'}`} />
                    </div>
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {offset.topic.replace('ecommerce.public.', '')}
                      </div>
                      <div className="text-xs text-gray-500">Partition {offset.partition}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium text-gray-900">
                      Lag: <span className={getLagColor(offset.lag || 0)}>{offset.lag || 0}</span>
                    </div>
                    <div className="text-xs text-gray-500">
                      {offset.failed_count !== undefined ? `${offset.failed_count} failed` : 'Healthy'}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Failed Messages Section */}
        <div className="bg-white border rounded-lg">
          <div className="px-4 py-3 border-b bg-gray-50">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-gray-600" />
                <h2 className="text-sm font-medium text-gray-900">Failed Messages</h2>
              </div>
              <div className="flex gap-2">
                <select
                  value={selectedStatus}
                  onChange={(e) => setSelectedStatus(e.target.value)}
                  className="text-sm border border-gray-300 rounded-lg px-3 py-1.5 bg-white"
                >
                  <option value="all">All Status</option>
                  <option value="pending">Pending</option>
                  <option value="retrying">Retrying</option>
                  <option value="resolved">Resolved</option>
                  <option value="dead_letter">Dead Letter</option>
                  <option value="ignored">Ignored</option>
                </select>
                {totalPending > 0 && (
                  <button
                    onClick={retryAll}
                    disabled={retrying}
                    className="flex items-center gap-2 px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                  >
                    <RotateCcw className="w-3 h-3" />
                    Retry All ({totalPending})
                  </button>
                )}
              </div>
            </div>
          </div>

          <div className="p-4">
            {failedMessages.length === 0 ? (
              <div className="text-center py-12">
                <CheckCircle2 className="w-12 h-12 text-green-500 mx-auto mb-3" />
                <p className="text-sm text-gray-500">No failed messages found</p>
                <p className="text-xs text-gray-400 mt-1">All messages are processing successfully</p>
              </div>
            ) : (
              <div className="space-y-2">
                {failedMessages.map((msg) => {
                  const badge = getStatusBadge(msg.status)
                  return (
                    <div key={msg.id} className="border rounded-lg p-3 hover:bg-gray-50">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className={`text-xs font-medium px-2 py-1 rounded ${badge.bg} ${badge.text}`}>
                              {msg.status}
                            </span>
                            <span className="text-xs text-gray-500">
                              #{msg.id} • {msg.topic.replace('ecommerce.public.', '')} [P{msg.partition}@{msg.offset}]
                            </span>
                          </div>
                          <div className="text-sm mb-1">
                            <span className="font-medium text-red-600">{msg.error_type}</span>
                            <span className="text-gray-500 ml-2">•</span>
                            <span className="text-gray-600 ml-2 text-xs">{msg.error_message.substring(0, 80)}...</span>
                          </div>
                          <div className="flex items-center gap-4 text-xs text-gray-500">
                            <span>Retries: {msg.retry_count}/{msg.max_retries}</span>
                            <span>Failed: {new Date(msg.failed_at).toLocaleString()}</span>
                          </div>
                        </div>
                        {msg.status === 'pending' && (
                          <button
                            onClick={() => retryMessage(msg.id)}
                            disabled={retrying}
                            className="ml-3 flex items-center gap-1 px-3 py-1.5 text-xs bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                          >
                            <RotateCcw className="w-3 h-3" />
                            Retry
                          </button>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
