import { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Mail, Lock, Eye, EyeOff, Globe } from 'lucide-react';
import logoImg from '../assets/logo.png';
import { apiFetch } from '../utils/api';

const Login: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const queryParams = new URLSearchParams(location.search);
  const redirectPath = queryParams.get('redirect') || '/dashboard';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  
  const [errors, setErrors] = useState<{ email?: string; password?: string; general?: string }>({});

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: { email?: string; password?: string; general?: string } = {};
    
    if (!email) newErrors.email = "Email is required";
    if (!password) newErrors.password = "Password is required";
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    
    try {
      const response = await apiFetch('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password })
      });
      
      if (response.ok) {
        const data = await response.json();
        login(data.access_token, data.user, rememberMe);
        navigate(redirectPath);
      } else {
        setErrors({ general: 'Invalid email or password.' });
      }
    } catch (err) {
      setErrors({ general: 'Failed to connect to the server.' });
    }
  };

  const handleGoogleLogin = () => {
    setErrors({ general: "Google OAuth CONFIGURATION REQUIRED. Not available in demo." });
  };

  const handleAction = (e: React.MouseEvent, action: string) => {
    e.preventDefault();
    setErrors({ general: `${action} is not available in the local SIH demo.` });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-navy-950 relative overflow-hidden px-4 font-sans selection:bg-blue-500/30">
      {/* Background Gradients and Grid */}
      <div className="absolute inset-0 z-0">
        {/* Animated Gradient Simulation via slow rotating blobs if possible, keeping simple static here to guarantee performance */}
        <div className="absolute top-0 left-1/4 w-[800px] h-[800px] bg-blue-600/5 rounded-full blur-[150px] mix-blend-screen animate-pulse duration-10000" />
        <div className="absolute bottom-0 right-1/4 w-[600px] h-[600px] bg-cyan-600/5 rounded-full blur-[120px] mix-blend-screen" />
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.015)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.015)_1px,transparent_1px)] bg-[size:48px_48px] [mask-image:radial-gradient(ellipse_80%_80%_at_50%_50%,#000_20%,transparent_100%)]" />
      </div>

      <div className="bg-navy-800/90 backdrop-blur-sm border border-navy-600/50 rounded-2xl p-8 w-full max-w-md relative z-10 shadow-2xl shadow-black/50 transform transition-all animate-[scale-in_0.3s_ease-out_forwards]">
        
        <div className="text-center mb-8">
          <img src={logoImg} alt='AERO RECON-3D' className='h-12 w-auto mx-auto mb-6' />
          <h2 className="text-xl font-medium text-slate-400">Sign in to your account</h2>
        </div>

        <form onSubmit={handleLogin} className="space-y-5">
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
                placeholder="Enter your password"
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

          <div className="flex justify-between items-center mb-6">
            <label className="flex items-center gap-2 cursor-pointer group">
              <div className="relative flex items-center justify-center">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="appearance-none w-4 h-4 border border-navy-600 rounded bg-navy-900 checked:bg-blue-600 checked:border-blue-600 cursor-pointer transition-all peer"
                />
                <svg className="absolute w-3 h-3 text-white opacity-0 peer-checked:opacity-100 pointer-events-none transition-opacity" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="3">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <span className="text-sm text-slate-400 group-hover:text-slate-300 transition-colors">Remember me</span>
            </label>
            <a href="#" onClick={(e) => handleAction(e, 'Password Reset')} className="text-blue-400 hover:text-blue-300 text-sm font-medium transition-colors">
              Forgot Password?
            </a>
          </div>

          <button
            type="submit"
            className="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold py-3 rounded-lg transition-all shadow-lg shadow-blue-600/20 active:scale-[0.98]"
          >
            Sign In
          </button>
          
          {errors.general && (
            <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
              <p className="text-red-400 text-sm text-center">{errors.general}</p>
            </div>
          )}
        </form>

        <div className="flex items-center gap-4 my-6">
          <div className="h-px bg-navy-600 flex-1"></div>
          <span className="text-slate-500 text-sm">or</span>
          <div className="h-px bg-navy-600 flex-1"></div>
        </div>

        <button
          onClick={handleGoogleLogin}
          type="button"
          className="w-full bg-navy-700 border border-navy-600 hover:bg-navy-600 text-slate-200 font-medium py-3 rounded-lg flex items-center justify-center gap-3 transition-all active:scale-[0.98]"
        >
          <Globe className="size-5" />
          Continue with Google
        </button>

        <p className="text-center mt-8 text-slate-400 text-sm">
          Don't have an account?{' '}
          <Link to="/register" className="text-blue-400 hover:text-blue-300 font-medium transition-colors">
            Create Account
          </Link>
        </p>
      </div>
      
      {/* Add custom scale-in animation utility if missing */}
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes scale-in {
          0% { transform: scale(0.95); opacity: 0; }
          100% { transform: scale(1); opacity: 1; }
        }
      `}} />
    </div>
  );
};

export default Login;
