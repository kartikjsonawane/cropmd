import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  ScanLine, BarChart3, MessageCircle, ShieldCheck,
  Leaf, ArrowRight, CheckCircle, Zap, Globe, Smartphone
} from 'lucide-react'

const features = [
  {
    icon: ScanLine,
    title: 'AI Disease Detection',
    desc: 'Upload a leaf photo and get instant diagnosis with 94%+ accuracy using ResNet-50 deep learning.',
    color: 'text-brand-600 bg-brand-50',
  },
  {
    icon: MessageCircle,
    title: 'AI Advisory Engine',
    desc: 'Receive personalized treatment plans, pesticide recommendations, and prevention tips.',
    color: 'text-blue-600 bg-blue-50',
  },
  {
    icon: BarChart3,
    title: 'Crop Health Analytics',
    desc: 'Track disease trends, monitor recovery, and visualize farm health over time.',
    color: 'text-purple-600 bg-purple-50',
  },
  {
    icon: ShieldCheck,
    title: 'Smart Alerts',
    desc: 'Get notified when disease severity rises or seasonal risk increases in your region.',
    color: 'text-orange-600 bg-orange-50',
  },
]

const stats = [
  { value: '38', label: 'Disease Classes' },
  { value: '94%+', label: 'Detection Accuracy' },
  { value: '54K+', label: 'Training Images' },
  { value: '4', label: 'Crop Types' },
]

const crops = ['Tomato', 'Potato', 'Corn', 'Pepper', 'Apple', 'Grape', 'Strawberry']

export default function Landing() {
  return (
    <div className="min-h-screen bg-white">
      {/* Navbar */}
      <nav className="border-b border-gray-100 bg-white/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-16">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-brand-600 rounded-lg flex items-center justify-center">
              <Leaf size={18} className="text-white" />
            </div>
            <span className="font-bold text-gray-900 text-lg">CropMD</span>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/login" className="btn-secondary text-sm py-2 px-4">Sign in</Link>
            <Link to="/register" className="btn-primary text-sm py-2 px-4">Get Started</Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden bg-gradient-to-br from-brand-50 via-white to-blue-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-24">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center max-w-4xl mx-auto"
          >
            <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-brand-100 text-brand-700 rounded-full text-sm font-medium mb-6">
              <Zap size={14} /> Powered by ResNet-50 Transfer Learning
            </div>
            <h1 className="text-5xl sm:text-6xl font-extrabold text-gray-900 tracking-tight mb-6 leading-tight">
              Detect Crop Diseases{' '}
              <span className="text-brand-600">Before They Spread</span>
            </h1>
            <p className="text-xl text-gray-600 mb-10 max-w-2xl mx-auto leading-relaxed">
              Upload a photo of your crop leaf and get an instant AI-powered diagnosis,
              treatment plan, and expert advisory — in seconds.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link to="/register" className="btn-primary text-base px-8 py-3.5 w-full sm:w-auto">
                Start Free Scan <ArrowRight size={18} />
              </Link>
              <Link to="/login" className="btn-secondary text-base px-8 py-3.5 w-full sm:w-auto">
                Sign In
              </Link>
            </div>
          </motion.div>

          {/* Stats */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.6 }}
            className="grid grid-cols-2 sm:grid-cols-4 gap-6 mt-20"
          >
            {stats.map(({ value, label }) => (
              <div key={label} className="text-center">
                <div className="text-3xl font-extrabold text-brand-600">{value}</div>
                <div className="text-sm text-gray-500 mt-1">{label}</div>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Everything a Modern Farmer Needs
            </h2>
            <p className="text-lg text-gray-500 max-w-2xl mx-auto">
              From disease detection to treatment planning — CropMD is your complete
              digital agronomist, available 24/7.
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map(({ icon: Icon, title, desc, color }, i) => (
              <motion.div
                key={title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="card p-6"
              >
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-4 ${color}`}>
                  <Icon size={22} />
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">{title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Supported Crops */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-3">Supported Crops</h2>
          <p className="text-gray-500 mb-8">Trained on the PlantVillage dataset with 54,000+ images</p>
          <div className="flex flex-wrap justify-center gap-3">
            {crops.map(crop => (
              <span key={crop} className="px-4 py-2 bg-white border border-gray-200 rounded-full text-sm font-medium text-gray-700 shadow-sm">
                {crop}
              </span>
            ))}
            <span className="px-4 py-2 bg-brand-50 border border-brand-200 rounded-full text-sm font-medium text-brand-700">
              +more
            </span>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">How It Works</h2>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { step: '01', title: 'Upload a Leaf Photo', desc: 'Take a photo of the affected crop leaf and upload it to CropMD.', icon: Smartphone },
              { step: '02', title: 'AI Analysis', desc: 'Our ResNet-50 model analyzes the image and identifies the disease with confidence scoring.', icon: Zap },
              { step: '03', title: 'Get Treatment Plan', desc: 'Receive a detailed advisory with treatments, pesticides, and prevention tips.', icon: CheckCircle },
            ].map(({ step, title, desc, icon: Icon }) => (
              <div key={step} className="text-center">
                <div className="w-14 h-14 bg-brand-600 rounded-2xl flex items-center justify-center mx-auto mb-5">
                  <Icon size={24} className="text-white" />
                </div>
                <div className="text-xs font-bold text-brand-600 mb-2 tracking-wider">STEP {step}</div>
                <h3 className="font-semibold text-gray-900 text-lg mb-2">{title}</h3>
                <p className="text-gray-500 text-sm leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-brand-600">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Protect Your Crops Today
          </h2>
          <p className="text-brand-100 text-lg mb-8">
            Join thousands of farmers using AI to safeguard their harvests.
          </p>
          <Link to="/register" className="inline-flex items-center gap-2 px-8 py-3.5 bg-white text-brand-700 font-semibold rounded-lg hover:bg-brand-50 transition-colors text-base">
            Create Free Account <ArrowRight size={18} />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-10">
        <div className="max-w-7xl mx-auto px-4 flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 bg-brand-600 rounded-md flex items-center justify-center">
              <Leaf size={15} className="text-white" />
            </div>
            <span className="font-bold text-white">CropMD</span>
          </div>
          <p className="text-sm">© 2024 CropMD. Built with ResNet-50, Flask & React.</p>
          <div className="flex items-center gap-2 text-sm">
            <Globe size={14} />
            <span>PlantVillage Dataset · 38 Disease Classes</span>
          </div>
        </div>
      </footer>
    </div>
  )
}
