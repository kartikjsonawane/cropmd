import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import api from '../api/axios'
import { formatDistanceToNow } from 'date-fns'
import { History as HistoryIcon, Search, Filter, Leaf, ArrowRight, ScanLine } from 'lucide-react'

function SeverityBadge({ severity }) {
  const map = { High: 'severity-high', Medium: 'severity-medium', Low: 'severity-low', None: 'severity-none' }
  return <span className={map[severity] || 'badge bg-gray-100 text-gray-600'}>{severity || 'N/A'}</span>
}

export default function History() {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['history', page, statusFilter],
    queryFn: () =>
      api.get(`/predictions/history?page=${page}&limit=20${statusFilter ? `&status=${statusFilter}` : ''}`).then(r => r.data),
    keepPreviousData: true,
  })

  const scans = data?.scans?.filter(s =>
    !search || s.prediction?.disease_name?.toLowerCase().includes(search.toLowerCase()) ||
    s.prediction?.crop_name?.toLowerCase().includes(search.toLowerCase())
  ) || []

  return (
    <div className="p-6 max-w-4xl mx-auto animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <HistoryIcon className="text-brand-600" size={24} /> Scan History
          </h1>
          <p className="text-gray-500 text-sm mt-1">{data?.total ?? 0} total scans</p>
        </div>
        <Link to="/scanner" className="btn-primary text-sm">
          <ScanLine size={16} /> New Scan
        </Link>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-5">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text" className="input pl-9 text-sm"
            placeholder="Search by disease or crop…"
            value={search} onChange={e => setSearch(e.target.value)}
          />
        </div>
        <select
          className="input w-36 text-sm"
          value={statusFilter}
          onChange={e => { setStatusFilter(e.target.value); setPage(1) }}
        >
          <option value="">All Status</option>
          <option value="active">Active</option>
          <option value="resolved">Resolved</option>
        </select>
      </div>

      {/* Scan List */}
      {isLoading ? (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="card p-4 animate-pulse">
              <div className="flex gap-4">
                <div className="w-16 h-16 bg-gray-100 rounded-xl" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-gray-100 rounded w-1/3" />
                  <div className="h-3 bg-gray-100 rounded w-1/2" />
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : scans.length > 0 ? (
        <div className="space-y-3">
          {scans.map(scan => (
            <Link
              key={scan.id}
              to={`/results/${scan.id}`}
              className="card p-4 flex items-center gap-4 hover:border-brand-200 hover:shadow-md transition-all"
            >
              {scan.image_url ? (
                <img src={scan.image_url} alt="" className="w-16 h-16 rounded-xl object-cover flex-shrink-0" />
              ) : (
                <div className="w-16 h-16 rounded-xl bg-brand-50 flex items-center justify-center flex-shrink-0">
                  <Leaf size={22} className="text-brand-300" />
                </div>
              )}
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-2 mb-1">
                  <span className="font-semibold text-gray-900">{scan.prediction?.disease_name}</span>
                  <SeverityBadge severity={scan.prediction?.severity} />
                </div>
                <div className="text-sm text-gray-500">
                  {scan.prediction?.crop_name} · {formatDistanceToNow(new Date(scan.created_at), { addSuffix: true })}
                </div>
                {scan.notes && <div className="text-xs text-gray-400 mt-1 truncate">{scan.notes}</div>}
              </div>
              <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
                <span className="text-lg font-bold text-gray-700">
                  {Math.round((scan.prediction?.confidence || 0) * 100)}%
                </span>
                <ArrowRight size={16} className="text-gray-300" />
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="card p-16 text-center text-gray-400">
          <ScanLine size={48} className="mx-auto mb-3 text-gray-200" />
          <p className="font-medium text-gray-600">No scans found</p>
          <p className="text-sm mt-1">
            {search ? 'Try a different search term' : 'Upload your first crop photo to get started'}
          </p>
          {!search && (
            <Link to="/scanner" className="btn-primary mt-4 text-sm">Start Scanning</Link>
          )}
        </div>
      )}

      {/* Pagination */}
      {data?.pages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-6">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="btn-secondary text-sm py-2 px-3 disabled:opacity-40"
          >
            Previous
          </button>
          <span className="text-sm text-gray-500">Page {page} of {data.pages}</span>
          <button
            onClick={() => setPage(p => Math.min(data.pages, p + 1))}
            disabled={page === data.pages}
            className="btn-secondary text-sm py-2 px-3 disabled:opacity-40"
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}
