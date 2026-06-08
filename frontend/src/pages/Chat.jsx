import { useState, useRef, useEffect } from 'react'
import api from '../api/axios'
import { Send, Bot, User, Loader2, MessageCircle, Trash2 } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { formatDistanceToNow } from 'date-fns'
import toast from 'react-hot-toast'

const SUGGESTIONS = [
  'How do I treat tomato early blight?',
  'What pesticide is safe for potatoes?',
  'How to prevent late blight in monsoon season?',
  'Best fertilizer for corn with rust disease?',
  'Is drip irrigation better for disease prevention?',
]

function MessageBubble({ msg }) {
  const isUser = msg.role === 'user'
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}
    >
      <div className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center ${
        isUser ? 'bg-brand-600' : 'bg-gray-100'
      }`}>
        {isUser ? <User size={16} className="text-white" /> : <Bot size={16} className="text-gray-600" />}
      </div>
      <div className={`max-w-[80%] ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
        <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
          isUser
            ? 'bg-brand-600 text-white rounded-tr-sm'
            : 'bg-gray-100 text-gray-800 rounded-tl-sm'
        }`}>
          {msg.content}
        </div>
        {msg.timestamp && (
          <span className="text-xs text-gray-400 px-1">
            {formatDistanceToNow(new Date(msg.timestamp), { addSuffix: true })}
          </span>
        )}
      </div>
    </motion.div>
  )
}

export default function Chat() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [convId, setConvId] = useState(null)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async (text) => {
    if (!text.trim() || loading) return
    const userMsg = { role: 'user', content: text, timestamp: new Date().toISOString() }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const { data } = await api.post('/chatbot/chat', {
        message: text,
        conversation_id: convId,
      })
      const botMsg = { role: 'assistant', content: data.reply, timestamp: new Date().toISOString() }
      setMessages(prev => [...prev, botMsg])
      if (data.conversation_id) setConvId(data.conversation_id)
    } catch (err) {
      toast.error('Chat failed. Please try again.')
      setMessages(prev => prev.slice(0, -1))
    } finally {
      setLoading(false)
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }

  const handleSubmit = e => {
    e.preventDefault()
    sendMessage(input)
  }

  const clearChat = () => {
    setMessages([])
    setConvId(null)
    toast.success('Conversation cleared')
  }

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] lg:h-screen max-w-3xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-white">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-brand-600 flex items-center justify-center">
            <Bot size={18} className="text-white" />
          </div>
          <div>
            <h1 className="font-semibold text-gray-900">CropMD AI Assistant</h1>
            <div className="flex items-center gap-1.5 text-xs text-gray-400">
              <div className="w-1.5 h-1.5 rounded-full bg-brand-500" />
              <span>Agricultural Expert · RAG-powered</span>
            </div>
          </div>
        </div>
        {messages.length > 0 && (
          <button onClick={clearChat} className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors">
            <Trash2 size={16} />
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 bg-brand-50 rounded-2xl flex items-center justify-center mb-4">
              <MessageCircle size={28} className="text-brand-500" />
            </div>
            <h2 className="font-semibold text-gray-900 mb-1">Ask CropMD Anything</h2>
            <p className="text-sm text-gray-400 mb-6 max-w-xs">
              Get expert advice on crop diseases, treatments, fertilizers, and farm management.
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              {SUGGESTIONS.map(s => (
                <button
                  key={s}
                  onClick={() => sendMessage(s)}
                  className="text-xs px-3 py-2 bg-gray-50 border border-gray-200 rounded-full text-gray-600 hover:bg-brand-50 hover:border-brand-200 hover:text-brand-700 transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg, i) => <MessageBubble key={i} msg={msg} />)}
            {loading && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
                  <Bot size={16} className="text-gray-600" />
                </div>
                <div className="bg-gray-100 rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-2">
                  <Loader2 size={14} className="animate-spin text-gray-400" />
                  <span className="text-sm text-gray-400">Thinking…</span>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </>
        )}
      </div>

      {/* Input */}
      <div className="px-4 py-4 border-t border-gray-200 bg-white">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            className="input flex-1"
            placeholder="Ask about crop diseases, treatments, fertilizers…"
            value={input}
            onChange={e => setInput(e.target.value)}
            disabled={loading}
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="btn-primary px-4 py-2.5 flex-shrink-0"
          >
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
          </button>
        </form>
        <p className="text-xs text-gray-400 mt-2 text-center">
          Powered by Gemini AI + Agricultural Knowledge Base
        </p>
      </div>
    </div>
  )
}
