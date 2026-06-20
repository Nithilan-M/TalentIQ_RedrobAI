import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Lock, Mail, ArrowRight, Briefcase, Eye, EyeOff } from "lucide-react";
import { authService } from "../services/auth";

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await authService.login(email, password);
      // Check if there are any JDs. If not, direct them to upload JD first
      navigate("/");
      // Force page reload to sync Navbar state
      window.location.reload();
    } catch (err: any) {
      setError(err.message || "Failed to log in. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center px-4 py-12 bg-slate-50">
      <div className="w-full max-w-md">
        {/* Flat Minimal Dashboard Box */}
        <div className="bg-white p-8 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex flex-col items-center mb-6">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-red-500 text-white shadow-sm">
              <Briefcase className="h-5 w-5" />
            </div>
            <h2 className="mt-4 text-center text-xl font-bold tracking-tight text-slate-900">
              Welcome Back
            </h2>
            <p className="mt-1 text-xs text-slate-500">
              Recruiter Access Portal
            </p>
          </div>

          {error && (
            <div className="mb-4 rounded-lg bg-red-50 p-3 border border-red-200 text-xs font-medium text-red-600">
              {error}
            </div>
          )}

          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-1">
                Email Address
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400">
                  <Mail className="h-4 w-4" />
                </span>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@company.com"
                  className="h-10 w-full rounded-md border border-slate-200 bg-white py-2 pl-9 pr-3 text-sm outline-none transition-all focus:border-red-500 focus:ring-1 focus:ring-red-500 text-slate-900 placeholder:text-slate-400"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-1">
                Password
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400">
                  <Lock className="h-4 w-4" />
                </span>
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="h-10 w-full rounded-md border border-slate-200 bg-white py-2 pl-9 pr-10 text-sm outline-none transition-all focus:border-red-500 focus:ring-1 focus:ring-red-500 text-slate-900 placeholder:text-slate-400"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 flex items-center pr-3 text-slate-400 hover:text-slate-600 transition-colors"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="flex h-10 w-full items-center justify-center space-x-1.5 rounded-md bg-red-500 hover:bg-red-600 text-sm font-medium text-white shadow-sm focus:outline-none transition-all disabled:opacity-50 cursor-pointer"
            >
              {loading ? (
                <span>Signing in...</span>
              ) : (
                <>
                  <span>Sign In</span>
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </form>

          <div className="mt-6 text-center text-xs">
            <span className="text-slate-500">Don't have an account? </span>
            <Link to="/register" className="font-semibold text-red-500 hover:text-red-600">
              Create account
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
