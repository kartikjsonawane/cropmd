import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { useNavigate } from 'react-router-dom'
import api from '../api/axios'
import toast from 'react-hot-toast'
import { Upload, ScanLine, X, Loader2, ImageIcon, AlertCircle } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

const MAX_SIZE = 10 * 1024 * 1024 // 10MB

export default function Scanner() {
  const navigate = useNavigate()
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [loading, setLoading] = useState(false)
  const [farmId, setFarmId] = useState('')
  const [notes, setNotes] = useState('')

  const onDrop = useCallback(accepted => {
    const f = accepted[0]
    if (!f) return
    setFile(f)
    setPreview(URL.createObjectURL(f))
  }, [])

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.jpg', '.jpeg', '.png', '.webp'] },
    maxSize: MAX_SIZE,
    maxFiles: 1,
  })

  const clearFile = e => {
    e.stopPropagation()
    setFile(null)
    if (preview) URL.revokeObjectURL(preview)
    setPreview(null)
  }

  const handleAnalyze = async () => {
    if (!file) { toast.error('Please select an image first'); return }
    setLoading(true)
    try {
      const form = new FormData()
      form.append('image', file)
      if (farmId) form.append('farm_id', farmId)
      if (notes) form.append('notes', notes)

      // Try to get GPS
      try {
        const pos = await new Promise((res, rej) =>
          navigator.geolocation.getCurrentPosition(res, rej, { timeout: 3000 })
        )
        form.append('lat', pos.coords.latitude)
        form.append('lng', pos.coords.longitude)
      } catch {}

      const { data } = await api.post('/predictions/analyze', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 60000,
      })
      toast.success('Analysis complete!')
      navigate(`/results/${data.scan_id}`)
    } catch (err) {
      toast.error(err.response?.data?.error || 'Analysis failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 max-w-2xl mx-auto animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <ScanLine className="text-brand-600" size={24} /> Disease Scanner
        </h1>
        <p className="text-gray-500 text-sm mt-1">
          Upload a clear photo of the affected crop leaf for AI analysis
        </p>
      </div>

      {/* Upload Zone */}
      <div className="card p-6 mb-4">
        <AnimatePresence mode="wait">
          {!preview ? (
            <motion.div
              key="dropzone"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              {...getRootProps()}
              className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors ${
                isDragActive
                  ? 'border-brand-500 bg-brand-50'
                  : 'border-gray-200 hover:border-brand-300 hover:bg-gray-50'
              }`}
            >
              <input {...getInputProps()} />
              <div className="w-16 h-16 bg-brand-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Upload size={28} className="text-brand-500" />
              </div>
              <p className="font-semibold text-gray-700 mb-1">
                {isDragActive ? 'Drop the image here' : 'Drag & drop or click to upload'}
              </p>
              <p className="text-sm text-gray-400">JPG, PNG, WEBP up to 10MB</p>

              {fileRejections.length > 0 && (
                <div className="mt-3 flex items-center gap-1.5 justify-center text-red-600 text-sm">
                  <AlertCircle size={14} />
                  {fileRejections[0].errors[0].message}
                </div>
              )}
            </motion.div>
          ) : (
            <motion.div
              key="preview"
              initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
              className="relative"
            >
              <img
                src={preview}
                alt="Preview"
                className="w-full max-h-80 object-contain rounded-xl bg-gray-50"
              />
              <button
                onClick={clearFile}
                className="absolute top-2 right-2 p-1.5 bg-white rounded-full shadow-md hover:bg-gray-100 transition-colors"
              >
                <X size={16} className="text-gray-600" />
              </button>
              <div className="mt-3 flex items-center gap-2 text-sm text-gray-600">
                <ImageIcon size={14} />
                <span className="truncate">{file.name}</span>
                <span className="text-gray-400">({(file.size / 1024 / 1024).toFixed(1)} MB)</span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Optional fields */}
      <div className="card p-6 mb-4 space-y-4">
        <h3 className="font-medium text-gray-700 text-sm">Optional Details</h3>
        <div>
          <label className="label">Notes</label>
          <textarea
            className="input resize-none h-20"
            placeholder="Describe symptoms, when noticed, area affected…"
            value={notes}
            onChange={e => setNotes(e.target.value)}
          />
        </div>
      </div>

      {/* Guidelines */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6">
        <h3 className="text-sm font-medium text-blue-800 mb-2">📸 Photo Tips for Best Results</h3>
        <ul className="text-xs text-blue-700 space-y-1.5">
          <li>• Use good natural lighting — avoid shadows on the leaf</li>
          <li>• Fill 70-80% of the frame with the leaf</li>
          <li>• Show both the front side and any spots/lesions clearly</li>
          <li>• Keep the camera steady — avoid blurry images</li>
          <li>• For early blight, focus on the characteristic ring patterns</li>
        </ul>
      </div>

      {/* Analyze Button */}
      <button
        onClick={handleAnalyze}
        disabled={!file || loading}
        className="btn-primary w-full justify-center py-3.5 text-base"
      >
        {loading ? (
          <><Loader2 size={18} className="animate-spin" /> Analyzing with AI…</>
        ) : (
          <><ScanLine size={18} /> Analyze Crop Disease</>
        )}
      </button>

      {loading && (
        <div className="mt-4 card p-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 border-3 border-brand-200 border-t-brand-600 rounded-full animate-spin flex-shrink-0" />
            <div>
              <p className="text-sm font-medium text-gray-700">Running AI Analysis</p>
              <p className="text-xs text-gray-400">ResNet-50 model processing your image…</p>
            </div>
          </div>
          <div className="mt-3 h-1.5 bg-gray-100 rounded-full overflow-hidden">
            <div className="h-full bg-brand-500 rounded-full animate-pulse-slow w-3/4" />
          </div>
        </div>
      )}
    </div>
  )
}
