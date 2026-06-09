"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Sparkles, Mail, Lock, User, Eye, EyeOff, ArrowRight, Check } from "lucide-react";
import { authApi, userApi } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";

export default function RegisterPage() {
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const passwordChecks = [
    { label: "At least 8 characters", valid: password.length >= 8 },
    { label: "One uppercase letter", valid: /[A-Z]/.test(password) },
    { label: "One number", valid: /\d/.test(password) },
  ];

  const isPasswordValid = passwordChecks.every((c) => c.valid);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isPasswordValid) return;
    setError("");
    setLoading(true);

    try {
      const tokens = await authApi.signup({ email, password, name });
      const user = await userApi.getProfile(tokens.access_token);
      setAuth(tokens.access_token, tokens.refresh_token, user);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2 mb-4">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-500 to-accent-violet flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <span className="text-2xl font-bold">FinSight AI</span>
          </Link>
          <h1 className="text-xl text-surface-300">Create your account</h1>
        </div>

        <div className="glass-card p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="p-3 rounded-lg bg-accent-rose/10 border border-accent-rose/20 text-accent-rose text-sm">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="name" className="block text-sm font-medium text-surface-300 mb-1.5">
                Full Name
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-500" />
                <input
                  id="name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-surface-800 border border-surface-700 text-surface-100 placeholder-surface-500 focus:border-brand-500 focus:ring-1 focus:ring-brand-500/50 transition-colors"
                  placeholder="John Doe"
                />
              </div>
            </div>

            <div>
              <label htmlFor="reg-email" className="block text-sm font-medium text-surface-300 mb-1.5">
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-500" />
                <input
                  id="reg-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-surface-800 border border-surface-700 text-surface-100 placeholder-surface-500 focus:border-brand-500 focus:ring-1 focus:ring-brand-500/50 transition-colors"
                  placeholder="you@company.com"
                />
              </div>
            </div>

            <div>
              <label htmlFor="reg-password" className="block text-sm font-medium text-surface-300 mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-500" />
                <input
                  id="reg-password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full pl-10 pr-12 py-2.5 rounded-lg bg-surface-800 border border-surface-700 text-surface-100 placeholder-surface-500 focus:border-brand-500 focus:ring-1 focus:ring-brand-500/50 transition-colors"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-surface-500 hover:text-surface-300"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {/* Password strength indicators */}
              {password.length > 0 && (
                <div className="mt-2 space-y-1">
                  {passwordChecks.map((check, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <Check className={`w-3 h-3 ${check.valid ? "text-accent-emerald" : "text-surface-600"}`} />
                      <span className={`text-xs ${check.valid ? "text-accent-emerald" : "text-surface-500"}`}>
                        {check.label}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <button
              type="submit"
              disabled={loading || !isPasswordValid}
              className="w-full py-2.5 rounded-lg bg-brand-600 hover:bg-brand-500 text-white font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  Create Account
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          <p className="text-center text-sm text-surface-500 mt-6">
            Already have an account?{" "}
            <Link href="/login" className="text-brand-400 hover:text-brand-300 font-medium">
              Sign in
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
