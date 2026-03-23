"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Users, FileText, CheckCircle2 } from "lucide-react";
import { adminApi } from "@/lib/api";

export default function AdminDashboardPage() {
  const [metrics, setMetrics] = useState<{
    total_users: number;
    total_interviews: number;
    average_score: number;
  } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMetrics();
  }, []);

  const loadMetrics = async () => {
    try {
      const data = await adminApi.getMetrics();
      setMetrics(data);
    } catch {
      // handled by api.ts error throw implicitly
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="spinner" style={{ margin: "40px auto" }} />;
  }

  return (
    <div>
      <h1 style={{ fontSize: "2rem", fontWeight: 700, marginBottom: "32px", color: "var(--text-primary)" }}>Platform Overview</h1>
      
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "24px", marginBottom: "40px" }}>
        {[
          { icon: Users, label: "Total Users", value: metrics?.total_users || 0, color: "#3b82f6" },
          { icon: FileText, label: "Total Interviews", value: metrics?.total_interviews || 0, color: "#8b5cf6" },
          { icon: CheckCircle2, label: "Platform Avg Score", value: metrics?.average_score !== null ? `${metrics?.average_score}%` : "—", color: "#10b981" },
        ].map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="glass-card"
            style={{ padding: "30px", display: "flex", alignItems: "center", gap: "20px" }}
          >
            <div style={{ width: "56px", height: "56px", borderRadius: "14px", background: `${stat.color}15`, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <stat.icon size={28} color={stat.color} />
            </div>
            <div>
              <div style={{ fontSize: "2rem", fontWeight: 700 }}>{stat.value}</div>
              <div style={{ color: "var(--text-muted)", fontSize: "0.95rem" }}>{stat.label}</div>
            </div>
          </motion.div>
        ))}
      </div>
      
      <div className="glass-card" style={{ padding: "40px", textAlign: "center", color: "var(--text-secondary)" }}>
        Welcome to the AI Interviewer tracking center.
        Use the sidebar to manage users or view deep analytics.
      </div>
    </div>
  );
}
