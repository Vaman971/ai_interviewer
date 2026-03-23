"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Brain,
  Plus,
  Clock,
  BarChart3,
  FileText,
  LogOut,
  Loader2,
  ChevronRight,
  Trash2,
  Shield,
} from "lucide-react";
import { useAuthStore } from "@/lib/stores";
import { interviewApi, type Interview } from "@/lib/api";
import toast from "react-hot-toast";

const statusColors: Record<string, string> = {
  created: "badge-info",
  analyzing: "badge-warning",
  questions_ready: "badge-purple",
  in_progress: "badge-warning",
  completed: "badge-success",
  scored: "badge-success",
  failed: "badge-error",
};

const statusLabels: Record<string, string> = {
  created: "Created",
  analyzing: "Analyzing...",
  questions_ready: "Ready",
  in_progress: "In Progress",
  completed: "Completed",
  scored: "Scored",
  failed: "Failed",
};

export default function DashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated, hydrate, logout } = useAuthStore();
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  useEffect(() => {
    if (!isAuthenticated) {
      const token = localStorage.getItem("access_token");
      if (!token) router.push("/login");
      return;
    }
    loadInterviews();
  }, [isAuthenticated, router]);

  const loadInterviews = async () => {
    try {
      const data = await interviewApi.list();
      setInterviews(data.interviews);
      setTotal(data.total);
    } catch {
      // Silently handle — user might need to re-login
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    router.push("/");
  };

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this interview session?")) return;
    
    try {
      await interviewApi.delete(id);
      toast.success("Interview deleted");
      setInterviews(prev => prev.filter(i => i.id !== id));
    } catch (err: unknown) {
      toast.error("Failed to delete interview");
    }
  };

  const completedCount = interviews.filter((i) => i.status === "scored").length;
  const avgScore = "—"; // Will come from API in future

  return (
    <div style={{ minHeight: "100vh" }}>
      {/* ── Top Bar ───────────────────────────────────────────── */}
      <nav style={{
        padding: "16px 24px",
        borderBottom: "1px solid var(--border-color)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        backdropFilter: "blur(20px)",
        background: "rgba(10, 10, 15, 0.8)",
        position: "sticky",
        top: 0,
        zIndex: 40,
      }}>
        <Link href="/dashboard" style={{ display: "flex", alignItems: "center", gap: "10px", textDecoration: "none" }}>
          <div style={{ width: "32px", height: "32px", borderRadius: "8px", background: "var(--accent-gradient)", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Brain size={18} color="white" />
          </div>
          <span style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--text-primary)" }}>AI Interviewer</span>
        </Link>
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          {user?.is_admin && (
            <Link href="/admin" className="btn-outline" style={{ padding: "6px 16px", fontSize: "0.85rem", textDecoration: "none", color: "var(--text-primary)" }}>
              <Shield size={14} style={{ marginRight: "6px" }} /> Admin
            </Link>
          )}
          <Link href="/dashboard/analytics" className="btn-outline" style={{ padding: "6px 16px", fontSize: "0.85rem", textDecoration: "none", color: "var(--text-primary)" }}>
            <BarChart3 size={14} style={{ marginRight: "6px" }} /> Analytics
          </Link>
          <span style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
            {user?.full_name || user?.email || "User"}
          </span>
          <button onClick={handleLogout} className="btn-outline" style={{ padding: "6px 16px", fontSize: "0.85rem" }}>
            <LogOut size={14} /> Logout
          </button>
        </div>
      </nav>

      {/* ── Content ───────────────────────────────────────────── */}
      <div style={{ maxWidth: "1100px", margin: "0 auto", padding: "40px 24px" }}>
        {/* Stats */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "20px", marginBottom: "40px" }}>
          {[
            { icon: FileText, label: "Total Interviews", value: total, color: "#7c3aed" },
            { icon: BarChart3, label: "Completed", value: completedCount, color: "#10b981" },
            { icon: Clock, label: "Avg Score", value: avgScore, color: "#06b6d4" },
          ].map((stat) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass-card"
              style={{ padding: "24px", display: "flex", alignItems: "center", gap: "16px" }}
            >
              <div style={{ width: "44px", height: "44px", borderRadius: "10px", background: `${stat.color}20`, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <stat.icon size={22} color={stat.color} />
              </div>
              <div>
                <div style={{ fontSize: "1.5rem", fontWeight: 700 }}>{stat.value}</div>
                <div style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>{stat.label}</div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Header + New Interview */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
          <h2 style={{ fontSize: "1.5rem", fontWeight: 700 }}>Your Interviews</h2>
          <Link href="/interview/setup" className="btn-gradient" style={{ textDecoration: "none" }}>
            <Plus size={18} /> New Interview
          </Link>
        </div>

        {/* Interview List */}
        {loading ? (
          <div style={{ textAlign: "center", padding: "60px 0" }}>
            <div className="spinner" style={{ margin: "0 auto 16px" }} />
            <p style={{ color: "var(--text-muted)" }}>Loading interviews...</p>
          </div>
        ) : interviews.length === 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="glass-card"
            style={{ padding: "60px 40px", textAlign: "center" }}
          >
            <FileText size={48} color="var(--text-muted)" style={{ margin: "0 auto 16px" }} />
            <h3 style={{ fontSize: "1.2rem", fontWeight: 600, marginBottom: "8px" }}>No Interviews Yet</h3>
            <p style={{ color: "var(--text-secondary)", marginBottom: "24px" }}>
              Start your first AI-powered interview practice session
            </p>
            <Link href="/interview/setup" className="btn-gradient" style={{ textDecoration: "none" }}>
              <Plus size={18} /> Create Your First Interview
            </Link>
          </motion.div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {interviews.map((interview, i) => (
              <motion.div
                key={interview.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className="glass-card"
                style={{ padding: "20px 24px", display: "flex", alignItems: "center", justifyContent: "space-between", cursor: "pointer" }}
                onClick={() => {
                  if (interview.status === "scored") {
                    router.push(`/interview/${interview.id}/results`);
                  } else if (interview.status === "created" || interview.status === "analyzing") {
                    toast.error("This interview setup is incomplete or still analyzing.");
                  } else {
                    router.push(`/interview/${interview.id}`);
                  }
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                  <div style={{ width: "40px", height: "40px", borderRadius: "10px", background: "var(--accent-gradient)", display: "flex", alignItems: "center", justifyContent: "center", opacity: 0.8 }}>
                    <FileText size={20} color="white" />
                  </div>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: "0.95rem" }}>
                      {interview.interview_type.charAt(0).toUpperCase() + interview.interview_type.slice(1)} Interview
                    </div>
                    <div style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>
                      {new Date(interview.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                      {interview.resume_filename && ` · ${interview.resume_filename}`}
                    </div>
                  </div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                  <span className={`badge ${statusColors[interview.status] || "badge-info"}`}>
                    {statusLabels[interview.status] || interview.status}
                  </span>
                  <button 
                    onClick={(e) => handleDelete(e, interview.id)} 
                    className="btn-outline" 
                    style={{ padding: "6px", color: "var(--error)", borderColor: "transparent", background: "transparent" }}
                    title="Delete Interview"
                  >
                    <Trash2 size={16} />
                  </button>
                  <ChevronRight size={18} color="var(--text-muted)" />
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
