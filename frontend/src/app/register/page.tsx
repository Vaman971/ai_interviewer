"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { Brain, Mail, Lock, User, ArrowRight, Loader2 } from "lucide-react";
import toast from "react-hot-toast";
import { authApi } from "@/lib/api";
import { useAuthStore } from "@/lib/stores";

export default function RegisterPage() {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      toast.error("Passwords do not match");
      return;
    }
    setLoading(true);
    try {
      await authApi.register(email, password, fullName || undefined);
      const { access_token } = await authApi.login(email, password);
      localStorage.setItem("access_token", access_token);
      const user = await authApi.getMe();
      setAuth(access_token, user);
      toast.success("Account created! Welcome aboard 🎉");
      router.push("/dashboard");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Registration failed";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", padding: "24px" }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="glass-card"
        style={{ width: "100%", maxWidth: "420px", padding: "40px" }}
      >
        <Link href="/" style={{ display: "flex", alignItems: "center", gap: "10px", justifyContent: "center", marginBottom: "32px", textDecoration: "none" }}>
          <div style={{ width: "40px", height: "40px", borderRadius: "10px", background: "var(--accent-gradient)", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Brain size={22} color="white" />
          </div>
          <span style={{ fontSize: "1.3rem", fontWeight: 700, color: "var(--text-primary)" }}>AI Interviewer</span>
        </Link>

        <h1 style={{ fontSize: "1.5rem", fontWeight: 700, textAlign: "center", marginBottom: "8px" }}>Create Account</h1>
        <p style={{ textAlign: "center", color: "var(--text-secondary)", marginBottom: "32px" }}>Start your interview prep journey</p>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
          <div>
            <label style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "6px", display: "block" }}>Full Name</label>
            <div style={{ position: "relative" }}>
              <User size={18} color="var(--text-muted)" style={{ position: "absolute", left: "14px", top: "50%", transform: "translateY(-50%)" }} />
              <input type="text" value={fullName} onChange={(e) => setFullName(e.target.value)} className="input-field" placeholder="John Doe" style={{ paddingLeft: "42px" }} />
            </div>
          </div>

          <div>
            <label style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "6px", display: "block" }}>Email</label>
            <div style={{ position: "relative" }}>
              <Mail size={18} color="var(--text-muted)" style={{ position: "absolute", left: "14px", top: "50%", transform: "translateY(-50%)" }} />
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="input-field" placeholder="you@example.com" required style={{ paddingLeft: "42px" }} />
            </div>
          </div>

          <div>
            <label style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "6px", display: "block" }}>Password</label>
            <div style={{ position: "relative" }}>
              <Lock size={18} color="var(--text-muted)" style={{ position: "absolute", left: "14px", top: "50%", transform: "translateY(-50%)" }} />
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="input-field" placeholder="Min. 8 characters" required minLength={8} style={{ paddingLeft: "42px" }} />
            </div>
          </div>

          <div>
            <label style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "6px", display: "block" }}>Confirm Password</label>
            <div style={{ position: "relative" }}>
              <Lock size={18} color="var(--text-muted)" style={{ position: "absolute", left: "14px", top: "50%", transform: "translateY(-50%)" }} />
              <input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} className="input-field" placeholder="••••••••" required minLength={8} style={{ paddingLeft: "42px" }} />
            </div>
          </div>

          <button type="submit" className="btn-gradient" disabled={loading} style={{ width: "100%", justifyContent: "center", padding: "14px" }}>
            {loading ? <Loader2 size={18} className="animate-spin" /> : <>Create Account <ArrowRight size={16} /></>}
          </button>
        </form>

        <p style={{ textAlign: "center", marginTop: "24px", fontSize: "0.9rem", color: "var(--text-secondary)" }}>
          Already have an account?{" "}
          <Link href="/login" style={{ color: "var(--accent-primary)", textDecoration: "none", fontWeight: 600 }}>Sign In</Link>
        </p>
      </motion.div>
    </div>
  );
}
