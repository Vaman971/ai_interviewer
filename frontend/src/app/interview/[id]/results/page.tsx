"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Award,
  Target,
  MessageSquare,
  Brain,
  TrendingUp,
  BookOpen,
  Loader2,
  Home,
} from "lucide-react";
import { interviewApi, type InterviewResult } from "@/lib/api";
import { useAuthStore } from "@/lib/stores";

export default function ResultsPage() {
  const params = useParams();
  const router = useRouter();
  const interviewId = params.id as string;
  const { hydrate } = useAuthStore();
  const [result, setResult] = useState<InterviewResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { hydrate(); }, [hydrate]);

  useEffect(() => {
    if (!localStorage.getItem("access_token")) {
      router.push("/login");
      return;
    }
    loadResults();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const loadResults = async () => {
    try {
      const data = await interviewApi.getResults(interviewId);
      setResult(data);
    } catch {
      // May not be ready yet
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score: number | null) => {
    if (!score) return "var(--text-muted)";
    if (score >= 80) return "#10b981";
    if (score >= 60) return "#f59e0b";
    return "#ef4444";
  };

  const getGrade = (score: number | null) => {
    if (!score) return "—";
    if (score >= 90) return "A+";
    if (score >= 85) return "A";
    if (score >= 80) return "A-";
    if (score >= 75) return "B+";
    if (score >= 70) return "B";
    if (score >= 65) return "B-";
    if (score >= 60) return "C+";
    if (score >= 55) return "C";
    return "D";
  };

  const parseJSON = (str: string | null): string | string[] | Record<string, unknown> | null => {
    if (!str) return null;
    try { return JSON.parse(str); } catch { return str; }
  };

  if (loading) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ textAlign: "center" }}>
          <div className="spinner" style={{ margin: "0 auto 16px" }} />
          <p style={{ color: "var(--text-muted)" }}>Loading results...</p>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div className="glass-card" style={{ padding: "40px", textAlign: "center", maxWidth: "400px" }}>
          <Award size={48} color="var(--text-muted)" style={{ marginBottom: "16px" }} />
          <h2 style={{ marginBottom: "8px" }}>Results Not Ready</h2>
          <p style={{ color: "var(--text-secondary)", marginBottom: "24px" }}>
            Complete the interview first to see your results.
          </p>
          <Link href={`/interview/${interviewId}`} className="btn-gradient" style={{ textDecoration: "none" }}>
            Go to Interview
          </Link>
        </div>
      </div>
    );
  }

  const feedback = parseJSON(result.feedback);
  const strengths = parseJSON(result.strengths);
  const weaknesses = parseJSON(result.weaknesses);
  const improvementPlan = parseJSON(result.improvement_plan);

  const scoreCategories = [
    { label: "Technical", score: result.technical_score, icon: Brain, color: "#7c3aed" },
    { label: "Behavioral", score: result.behavioral_score, icon: MessageSquare, color: "#06b6d4" },
    { label: "Communication", score: result.communication_score, icon: Target, color: "#10b981" },
    { label: "Problem Solving", score: result.problem_solving_score, icon: TrendingUp, color: "#f59e0b" },
  ];

  return (
    <div style={{ minHeight: "100vh" }}>
      {/* Nav */}
      <nav style={{ padding: "16px 24px", borderBottom: "1px solid var(--border-color)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <Link href="/dashboard" style={{ color: "var(--text-muted)", display: "flex" }}>
            <ArrowLeft size={18} />
          </Link>
          <Award size={20} color="var(--accent-primary)" />
          <span style={{ fontWeight: 600 }}>Interview Results</span>
        </div>
        <Link href="/dashboard" className="btn-outline" style={{ padding: "8px 16px", textDecoration: "none", fontSize: "0.85rem" }}>
          <Home size={14} /> Dashboard
        </Link>
      </nav>

      <div style={{ maxWidth: "900px", margin: "40px auto", padding: "0 24px" }}>
        {/* Overall Score */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card"
          style={{
            padding: "40px",
            textAlign: "center",
            marginBottom: "32px",
            background: "linear-gradient(135deg, rgba(124,58,237,0.08) 0%, rgba(6,182,212,0.08) 100%)",
          }}
        >
          <div className="score-circle" style={{ margin: "0 auto 20px" }}>
            <div className="score-circle-inner">
              <span style={{ color: getScoreColor(result.overall_score) }}>
                {result.overall_score?.toFixed(0) || "—"}
              </span>
            </div>
          </div>
          <div style={{ fontSize: "2rem", fontWeight: 800, marginBottom: "4px" }}>
            Grade: <span className="gradient-text">{getGrade(result.overall_score)}</span>
          </div>
          <p style={{ color: "var(--text-secondary)" }}>
            {result.questions_answered || 0} of {result.total_questions || 0} questions answered
          </p>
        </motion.div>

        {/* Score Breakdown */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "16px", marginBottom: "32px" }}>
          {scoreCategories.map((cat, i) => (
            <motion.div
              key={cat.label}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className="glass-card"
              style={{ padding: "24px" }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "16px" }}>
                <div style={{ width: "40px", height: "40px", borderRadius: "10px", background: `${cat.color}20`, display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <cat.icon size={20} color={cat.color} />
                </div>
                <span style={{ fontWeight: 600 }}>{cat.label}</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                <div style={{ flex: 1, height: "8px", borderRadius: "4px", background: "var(--bg-secondary)" }}>
                  <div style={{
                    height: "100%",
                    borderRadius: "4px",
                    background: cat.color,
                    width: `${cat.score || 0}%`,
                    transition: "width 1s ease",
                  }} />
                </div>
                <span style={{ fontWeight: 700, fontSize: "1.1rem", color: getScoreColor(cat.score), minWidth: "40px" }}>
                  {cat.score?.toFixed(0) || "—"}
                </span>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Strengths & Weaknesses */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "32px" }}>
          {/* Strengths */}
          <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} className="glass-card" style={{ padding: "24px" }}>
            <h3 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "16px", display: "flex", alignItems: "center", gap: "8px" }}>
              <TrendingUp size={18} color="var(--success)" /> Strengths
            </h3>
            {Array.isArray(strengths) && strengths.length > 0 ? (
              <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: "10px" }}>
                {strengths.map((s, i) => (
                  <li key={i} style={{ display: "flex", gap: "8px", color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                    <span style={{ color: "var(--success)" }}>✓</span> {s}
                  </li>
                ))}
              </ul>
            ) : (
              <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>Data will appear after scoring</p>
            )}
          </motion.div>

          {/* Weaknesses */}
          <motion.div initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} className="glass-card" style={{ padding: "24px" }}>
            <h3 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "16px", display: "flex", alignItems: "center", gap: "8px" }}>
              <Target size={18} color="var(--warning)" /> Areas to Improve
            </h3>
            {Array.isArray(weaknesses) && weaknesses.length > 0 ? (
              <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: "10px" }}>
                {weaknesses.map((w, i) => (
                  <li key={i} style={{ display: "flex", gap: "8px", color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                    <span style={{ color: "var(--warning)" }}>→</span> {w}
                  </li>
                ))}
              </ul>
            ) : (
              <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>Data will appear after scoring</p>
            )}
          </motion.div>
        </div>

        {/* Feedback */}
        {feedback && (
          <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} className="glass-card" style={{ padding: "24px", marginBottom: "32px" }}>
            <h3 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "12px", display: "flex", alignItems: "center", gap: "8px" }}>
              <MessageSquare size={18} color="var(--accent-primary)" /> Detailed Feedback
            </h3>
            <p style={{ color: "var(--text-secondary)", lineHeight: 1.7, whiteSpace: "pre-wrap" }}>
              {typeof feedback === "string" ? feedback : JSON.stringify(feedback, null, 2)}
            </p>
          </motion.div>
        )}

        {/* Improvement Plan */}
        {improvementPlan && (
          <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} className="glass-card" style={{ padding: "24px", marginBottom: "32px" }}>
            <h3 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "12px", display: "flex", alignItems: "center", gap: "8px" }}>
              <BookOpen size={18} color="var(--accent-secondary)" /> 30-Day Improvement Plan
            </h3>
            <p style={{ color: "var(--text-secondary)", lineHeight: 1.7, whiteSpace: "pre-wrap" }}>
              {typeof improvementPlan === "string" ? improvementPlan : JSON.stringify(improvementPlan, null, 2)}
            </p>
          </motion.div>
        )}

        {/* Back to Dashboard */}
        <div style={{ textAlign: "center", paddingBottom: "40px" }}>
          <Link href="/interview/setup" className="btn-gradient" style={{ textDecoration: "none", marginRight: "12px" }}>
            New Interview
          </Link>
          <Link href="/dashboard" className="btn-outline" style={{ textDecoration: "none" }}>
            Back to Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
