import React, { useEffect, useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { Briefcase, Sun, Moon, LogOut, BarChart2, Upload, Users, Sparkles } from "lucide-react";
import { authService } from "../services/auth";
import { apiService } from "../services/api";

interface NavbarProps {
  isDark: boolean;
  toggleTheme: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ isDark, toggleTheme }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [jds, setJds] = useState<{ id: number; title: string }[]>([]);
  const [activeJdId, setActiveJdId] = useState<string>("");

  useEffect(() => {
    if (authService.isAuthenticated()) {
      fetchJds();
      const savedJd = localStorage.getItem("active_jd_id") || "";
      setActiveJdId(savedJd);
    }
  }, [location.pathname]);

  const fetchJds = async () => {
    try {
      const data = await apiService.listJobDescriptions();
      setJds(data);
      if (data.length > 0 && !localStorage.getItem("active_jd_id")) {
        localStorage.setItem("active_jd_id", String(data[0].id));
        setActiveJdId(String(data[0].id));
      }
    } catch (err) {
      console.error("Failed to load job descriptions:", err);
    }
  };

  const handleJdChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    localStorage.setItem("active_jd_id", val);
    setActiveJdId(val);
    // Reload page to refresh all active queries
    window.location.reload();
  };

  const handleLogout = () => {
    authService.logout();
    navigate("/login");
  };

  const isActive = (path: string) => location.pathname === path;

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-slate-200 bg-white">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-14 items-center justify-between">
          {/* Logo */}
          <div className="flex items-center space-x-2.5 cursor-pointer" onClick={() => navigate("/")}>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-red-500 text-white shadow-sm">
              <Briefcase className="h-4.5 w-4.5" />
            </div>
            <span className="text-[#111827] text-base font-semibold tracking-tight">
              AI Hiring Committee
            </span>
          </div>

          {/* Navigation Links */}
          {authService.isAuthenticated() && (
            <div className="hidden md:flex space-x-1">
              <Link
                to="/"
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  isActive("/")
                    ? "bg-slate-100 text-slate-900"
                    : "text-slate-500 hover:text-slate-900 hover:bg-slate-50"
                }`}
              >
                <Users className="h-4 w-4" />
                <span>Dashboard</span>
              </Link>
              <Link
                to="/challenge"
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  isActive("/challenge")
                    ? "bg-slate-100 text-slate-900"
                    : "text-slate-500 hover:text-slate-900 hover:bg-slate-50"
                }`}
              >
                <Sparkles className="h-4 w-4 text-purple-500" />
                <span>Redrob Challenge</span>
              </Link>
              <Link
                to="/upload-jd"
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  isActive("/upload-jd")
                    ? "bg-slate-100 text-slate-900"
                    : "text-slate-500 hover:text-slate-900 hover:bg-slate-50"
                }`}
              >
                <Upload className="h-4 w-4" />
                <span>Upload JD</span>
              </Link>

              <Link
                to="/upload-resume"
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  isActive("/upload-resume")
                    ? "bg-slate-100 text-slate-900"
                    : "text-slate-500 hover:text-slate-900 hover:bg-slate-50"
                }`}
              >
                <Briefcase className="h-4 w-4" />
                <span>Parse Resumes</span>
              </Link>
              <Link
                to="/analytics"
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  isActive("/analytics")
                    ? "bg-slate-100 text-slate-900"
                    : "text-slate-500 hover:text-slate-900 hover:bg-slate-50"
                }`}
              >
                <BarChart2 className="h-4 w-4" />
                <span>Analytics</span>
              </Link>
            </div>
          )}

          {/* Controls */}
          <div className="flex items-center space-x-3">
            {authService.isAuthenticated() && jds.length > 0 && (
              <div className="flex items-center space-x-1.5">
                <span className="text-xs text-slate-400 hidden lg:inline">Active Job:</span>
                <select
                  value={activeJdId}
                  onChange={handleJdChange}
                  className="rounded-md border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-700 outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500"
                >
                  {jds.map((jd) => (
                    <option key={jd.id} value={jd.id}>
                      {jd.title}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Log Out */}
            {authService.isAuthenticated() && (
              <button
                onClick={handleLogout}
                className="flex h-8 px-2.5 items-center justify-center space-x-1.5 rounded-md bg-white border border-slate-200 text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition-all text-xs font-medium"
              >
                <LogOut className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Log out</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
