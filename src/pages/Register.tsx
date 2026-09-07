import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Mail, Lock, Eye, EyeOff } from 'lucide-react';
import logoImg from '../assets/logo.png';
import { apiFetch } from '../utils/api';

const Register: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  
  const [errors, setErrors] = useState<{ email?: string; password?: string; confirmPassword?: string; general?: string }>({});

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: { email?: string; password?: string; confirmPassword?: string; general?: string } = {};
    
    if (!email) newErrors.email = "Email is required";
    if (!password) newErrors.password = "Password is required";
    else if (password.length < 6) newErrors.password = "Password must be at least 6 characters";
    
    if (!confirmPassword) newErrors.confirmPassword = "Confirm Password is required";
    else if (password !== confirmPassword) newErrors.confirmPassword = "Passwords do not match";
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    
    try {
      const response = await apiFetch('/auth/register', {
        method: 'POST',
        body: JSON.stringify({ email, password })
      });
      
      if (response.ok) {
        const data = await response.json();
        login(data.access_token, data.user, false);
        navigate('/dashboard');
      } else if (response.status === 409) {
        setErrors({ email: 'Email is already registered.' });
      } else {
        setErrors({ general: 'Failed to register account.' });
      }
    } catch (err) {
      setErrors({ general: 'Failed to connect to the server.' });
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-navy-950 relative overflow-hidden px-4 font-sans selection:bg-blue-500/30">
      {/* Background Gradients and Grid */}
      <div className="absolute inset-0 z-0">
        <div className="absolute top-0 left-1/4 w-[800px] h-[800px] bg-blue-600/5 rounded-full blur-[150px] mix-blend-screen animate-pulse duration-10000" />
        <div className="absolute bottom-0 right-1/4 w-[600px] h-[600px] bg-cyan-600/5 rounded-full blur-[120px] mix-blend-screen" />
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.015)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.015)_1px,transparent_1px)] bg-[size:48px_48px] [mask-image:radial-gradient(ellipse_80%_80%_at_50%_50%,#000_20%,transparent_100%)]" />
      </div>

      <div className="bg-navy-800/90 backdrop-blur-sm border border-navy-600/50 rounded-2xl p-8 w-full max-w-md relative z-10 shadow-2xl shadow-black/50 transform transition-all animate-[scale-in_0.3s_ease-out_forwards]">
        
        <div className="text-center mb-8">
          <img src={logoImg} alt='AERO RECON-3D' className='h-12 w-auto mx-auto mb-6' />
          <h2 className="text-xl font-medium text-slate-400">Create an account</h2>
        </div>

        <form onSubmit={handleRegister} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5" htmlFor="email">
              Email Address
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 size-4" />
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (errors.email) setErrors({ ...errors, email: undefined });
                }}
                className={`w-full bg-navy-900 border ${errors.email ? 'border-red-500 focus:ring-red-500/50' : 'border-navy-600 focus:border-blue-500 focus:ring-blue-500/50'} rounded-lg pl-10 pr-4 py-3 text-slate-100 placeholder-slate-500 outline-none transition-all focus:ring-1`}
                placeholder="Enter your email"
              />
            </div>
            {errors.email && <p className="text-red-400 text-xs mt-1.5">{errors.email}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5" htmlFor="password">
              Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 size-4" />
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (errors.password) setErrors({ ...errors, password: undefined });
                }}
                className={`w-full bg-navy-900 border ${errors.password ? 'border-red-500 focus:ring-red-500/50' : 'border-navy-600 focus:border-blue-500 focus:ring-blue-500/50'} rounded-lg pl-10 pr-10 py-3 text-slate-100 placeholder-slate-500 outline-none transition-all focus:ring-1`}
                placeholder="Create a password"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors focus:outline-none"
              >
                {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
              </button>
            </div>
            {errors.password && <p className="text-red-400 text-xs mt-1.5">{errors.password}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5" htmlFor="confirmPassword">
              Confirm Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 size-4" />
              <input
                id="confirmPassword"
                type={showPassword ? 'text' : 'password'}
                value={confirmPassword}
                onChange={(e) => {
                  setConfirmPassword(e.target.value);
                  if (errors.confirmPassword) setErrors({ ...errors, confirmPassword: undefined });
                }}
                className={`w-full bg-navy-900 border ${errors.confirmPassword ? 'border-red-500 focus:ring-red-500/50' : 'border-navy-600 focus:border-blue-500 focus:ring-blue-500/50'} rounded-lg pl-10 pr-10 py-3 text-slate-100 placeholder-slate-500 outline-none transition-all focus:ring-1`}
                placeholder="Confirm your password"
              />
            </div>
            {errors.confirmPassword && <p className="text-red-400 text-xs mt-1.5">{errors.confirmPassword}</p>}
          </div>

          <button
            type="submit"
            className="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold py-3 rounded-lg transition-all shadow-lg shadow-blue-600/20 active:scale-[0.98] mt-4"
          >
            Create Account
          </button>
          
          {errors.general && (
            <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
              <p className="text-red-400 text-sm text-center">{errors.general}</p>
            </div>
          )}
        </form>

        <p className="text-center mt-8 text-slate-400 text-sm">
          Already have an account?{' '}
          <Link to="/login" className="text-blue-400 hover:text-blue-300 font-medium transition-colors">
            Sign In
          </Link>
        </p>
      </div>
      
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes scale-in {
          0% { transform: scale(0.95); opacity: 0; }
          100% { transform: scale(1); opacity: 1; }
        }
      `}} />
    </div>
  );
};

export default Register;
