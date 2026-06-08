import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import api from '../api/axios'
import {
  ArrowLeft, CheckCircle, AlertTriangle, Info,
  Sprout, Droplets, FlaskConical, Shield, Leaf, ScanLine
} from 'lucide-react'
import { RadialBarChart, RadialBar, ResponsiveContainer, Cell } from 'recharts'

function SeverityBadge({ severity }) {
  const map = {
    High: 'severity-high', Medium: 'severity-medium',
    Low: 'severity-low', None: 'severity-none',
  }
  return <span className={map[severity] || 'badge bg-gray-100 text-gray-600'}>{severity || 'Unknown'}</span>
}

function ConfidenceGauge({ value }) {
  const pct = Math.round(value * 100)
  const color = pct >= 85 ? '#22c55e' : pct >= 60 ? '#f59e0b' : '#f43f5e'
  return (
    <div className="flex flex-col items-center">
      <div className="relative w-28 h-28">
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            innerRadius="70%" outerRadius="100%"
            data={[{ value: pct }]}
            startAngle={90} endAngle={90 - 360 * (pct / 100)}
          >
            <RadialBar dataKey="value" cornerRadius={6} background={{ fill: '#f3f4f6' }}>
              <Cell fill={color} />
            </RadialBar>
          </RadialBarChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-extrabold text-gray-900">{pct}%</span>
          <span className="text-xs text-gray-400">confidence</span>
        </div>
      </div>
    </div>
  )
}

export default function Results() {
  const { scanId } = useParams()
  const { data, isLoading, error } = useQuery({
    queryKey: ['scan', scanId],
    queryFn: () => api.get(`/predictions/${scanId}`).then(r => r.data.scan),
  })

  if (isLoading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-8 h-8 border-4 border-brand-200 border-t-brand-600 rounded-full animate-spin" />
    </div>
  )
  if (error || !data) return (
    <div className="p-6 text-center text-gray-500">Scan not found.</div>
  )

  const { prediction, advisory, image_url, created_at } = data
  const isHealthy = prediction?.is_healthy

  return (
    <div className="p-6 max-w-3xl mx-auto animate-fade-in">
      <Link to="/history" className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-6">
        <ArrowLeft size={16} /> Back to History
      </Link>

      {/* Hero Result */}
      <div className={`card p-6 mb-6 border-l-4 ${isHealthy ? 'border-l-brand-500' : 'border-l-red-500'}`}>
        <div className="flex flex-col sm:flex-row gap-6">
          {image_url && (
            <img src={image_url} alt="Scan" className="w-full sm:w-48 h-48 object-cover rounded-xl flex-shrink-0" />
          )}
          <div className="flex-1 space-y-3">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  {isHealthy
                    ? <CheckCircle size={20} className="text-brand-600" />
                    : <AlertTriangle size={20} className="text-red-500" />
                  }
                  <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                    {prediction?.crop_name}
                  </span>
                </div>
                <h1 className="text-xl font-bold text-gray-900">{prediction?.disease_name}</h1>
                <div className="flex items-center gap-2 mt-2">
                  <SeverityBadge severity={prediction?.severity} />
                </div>
              </div>
              <ConfidenceGauge value={prediction?.confidence || 0} />
            </div>

            {/* Top Predictions */}
            {prediction?.top_predictions?.length > 0 && (
              <div>
                <p className="text-xs text-gray-400 font-medium mb-2">TOP PREDICTIONS</p>
                <div className="space-y-1.5">
                  {prediction.top_predictions.slice(0, 3).map((p, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <div className="flex-1 bg-gray-100 rounded-full h-1.5 overflow-hidden">
                        <div
                          className="h-full bg-brand-500 rounded-full transition-all"
                          style={{ width: `${Math.round(p.confidence * 100)}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-600 w-12 text-right">
                        {Math.round(p.confidence * 100)}%
                      </span>
                      <span className="text-xs text-gray-500 w-36 truncate">{p.disease_name}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {isHealthy ? (
        <div className="card p-6 bg-brand-50 border-brand-200">
          <div className="flex items-center gap-3 mb-3">
            <Leaf size={20} className="text-brand-600" />
            <h2 className="font-semibold text-brand-900">Plant Appears Healthy!</h2>
          </div>
          <p className="text-sm text-brand-700">{advisory?.description || 'No visible signs of disease detected. Continue current management practices.'}</p>
          {advisory?.prevention?.length > 0 && (
            <div className="mt-4">
              <p className="text-xs font-semibold text-brand-800 mb-2">MAINTENANCE TIPS</p>
              <ul className="space-y-1.5">
                {advisory.prevention.map((tip, i) => (
                  <li key={i} className="text-sm text-brand-700 flex gap-2">
                    <span className="text-brand-400 mt-0.5">•</span>{tip}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {/* Description */}
          {advisory?.description && (
            <div className="card p-5">
              <h2 className="font-semibold text-gray-900 flex items-center gap-2 mb-3">
                <Info size={18} className="text-blue-500" /> About This Disease
              </h2>
              <p className="text-sm text-gray-600 leading-relaxed">{advisory.description}</p>
            </div>
          )}

          {/* Symptoms */}
          {advisory?.symptoms?.length > 0 && (
            <div className="card p-5">
              <h2 className="font-semibold text-gray-900 flex items-center gap-2 mb-3">
                <AlertTriangle size={18} className="text-orange-500" /> Symptoms
              </h2>
              <ul className="space-y-1.5">
                {advisory.symptoms.map((s, i) => (
                  <li key={i} className="text-sm text-gray-600 flex gap-2">
                    <span className="text-orange-400 mt-0.5 flex-shrink-0">•</span>{s}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Treatments */}
          {advisory?.treatments?.length > 0 && (
            <div className="card p-5">
              <h2 className="font-semibold text-gray-900 flex items-center gap-2 mb-3">
                <FlaskConical size={18} className="text-purple-500" /> Treatment Protocol
              </h2>
              <div className="space-y-3">
                {advisory.treatments.map((t, i) => (
                  <div key={i} className="bg-gray-50 rounded-lg p-3.5">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-gray-800 text-sm">{t.name}</span>
                      <span className="text-xs text-brand-600 bg-brand-50 px-2 py-0.5 rounded-full">{t.dosage}</span>
                    </div>
                    <p className="text-xs text-gray-500">{t.frequency} · {t.notes}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Prevention */}
          {advisory?.prevention?.length > 0 && (
            <div className="card p-5">
              <h2 className="font-semibold text-gray-900 flex items-center gap-2 mb-3">
                <Shield size={18} className="text-green-500" /> Prevention Measures
              </h2>
              <ul className="space-y-2">
                {advisory.prevention.map((p, i) => (
                  <li key={i} className="text-sm text-gray-600 flex gap-2">
                    <CheckCircle size={14} className="text-green-500 mt-0.5 flex-shrink-0" />{p}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Fertilizer & Irrigation */}
          <div className="grid sm:grid-cols-2 gap-4">
            {advisory?.fertilizer_tips?.length > 0 && (
              <div className="card p-5">
                <h2 className="font-semibold text-gray-900 flex items-center gap-2 mb-3">
                  <Sprout size={18} className="text-yellow-600" /> Fertilizer Tips
                </h2>
                <ul className="space-y-1.5">
                  {advisory.fertilizer_tips.map((tip, i) => (
                    <li key={i} className="text-xs text-gray-600 flex gap-2">
                      <span className="text-yellow-500 mt-0.5">•</span>{tip}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {advisory?.irrigation_tips && (
              <div className="card p-5">
                <h2 className="font-semibold text-gray-900 flex items-center gap-2 mb-3">
                  <Droplets size={18} className="text-blue-500" /> Irrigation
                </h2>
                <p className="text-xs text-gray-600 leading-relaxed">{advisory.irrigation_tips}</p>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="flex gap-3 mt-6">
        <Link to="/scanner" className="btn-primary flex-1 justify-center">
          <ScanLine size={16} /> New Scan
        </Link>
        <Link to="/chat" className="btn-secondary flex-1 justify-center">
          Ask AI Chat
        </Link>
      </div>
    </div>
  )
}
