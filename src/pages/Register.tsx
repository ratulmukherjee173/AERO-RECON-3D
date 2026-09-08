import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Logo } from '../components/shared/Logo';
import { useAuth } from '../contexts/AuthContext';
import { apiFetch } from '../utils/api';
import { Mail, Lock, User, Eye, EyeOff, Loader2 } from 'lucide-react';

export default function Register() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setIsLoading(true);

    try {
      const response = await apiFetch('/auth/register', {
        method: 'POST',
        body: JSON.stringify({ email, password, name })
      });
      
      const data = await response.json();
      login(data.access_token, { id: data.user_id, email: data.email, name: data.name }, true);
      navigate('/dashboard');
    } catch (err: any) {
      if (err.message.includes('fetch')) {
        setError('Network error: Cannot reach the authentication server.');
      } else {
        setError(err.message || 'Failed to create account.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-navy-950 flex flex-col items-center justify-center p-4 relative overflow-hidden">
      {/* Background aesthetics */}
      <div className="absolute top-[-20%] right-[-10%] w-[50%] h-[50%] bg-cyan-900/20 blur-[120px] rounded-full mix-blend-screen pointer-events-none"></div>
      <div className="absolute bottom-[-20%] left-[-10%] w-[50%] h-[50%] bg-blue-900/20 blur-[120px] rounded-full mix-blend-screen pointer-events-none"></div>

      <div className="w-full max-w-md relative z-10">
        <div className="text-center mb-8">
          <div className="flex justify-center mb-6">
            <Logo size="lg" />
          </div>
          <h1 className="text-2xl font-bold tracking-widest uppercase text-slate-100">Create Account</h1>
          <p className="text-slate-400 mt-2 text-sm tracking-wide">Join AERO RECON-3D to save your projects</p>
        </div>

        <div className="bg-navy-900/80 backdrop-blur-xl border border-navy-700 p-8 rounded-2xl shadow-2xl">
          {error && (
            <div className="mb-6 p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-sm font-medium">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-xs font-bold tracking-widest uppercase text-slate-400 mb-2">Full Name</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-[#050A15] border border-navy-700 rounded-xl pl-10 pr-4 py-3 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/30 transition-all"
                  placeholder="John Doe"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold tracking-widest uppercase text-slate-400 mb-2">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-[#050A15] border border-navy-700 rounded-xl pl-10 pr-4 py-3 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/30 transition-all"
                  placeholder="name@company.com"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold tracking-widest uppercase text-slate-400 mb-2">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-[#050A15] border border-navy-700 rounded-xl pl-10 pr-12 py-3 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/30 transition-all"
                  placeholder="••••••••"
                  required
                  minLength={8}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold tracking-widest uppercase text-slate-400 mb-2">Confirm Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full bg-[#050A15] border border-navy-700 rounded-xl pl-10 pr-12 py-3 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/30 transition-all"
                  placeholder="••••••••"
                  required
                  minLength={8}
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full mt-6 py-3 px-4 bg-cyan-500 hover:bg-cyan-400 text-navy-950 font-bold tracking-widest uppercase rounded-xl transition-all shadow-[0_0_20px_rgba(34,211,238,0.2)] hover:shadow-[0_0_30px_rgba(34,211,238,0.4)] disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center h-12"
            >
              {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'CREATE ACCOUNT'}
            </button>
          </form>

          <div className="mt-8 text-center border-t border-navy-700/50 pt-6">
            <p className="text-sm text-slate-400">
              Already have an account?{' '}
              <Link to="/login" className="text-cyan-500 font-semibold hover:text-cyan-400 hover:underline transition-colors">
                Sign In
              </Link>
            </p>
            <p className="text-sm text-slate-500 mt-4">
              <Link to="/dashboard" className="hover:text-slate-300 transition-colors">Return to Dashboard (Guest Mode)</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
