"use client";

import { motion } from "framer-motion";
import {
  Brain,
  Mic,
  BarChart3,
  Code2,
  ArrowRight,
  Sparkles,
  Shield,
  Zap,
} from "lucide-react";
import Link from "next/link";

const features = [
  {
    icon: Brain,
    title: "AI-Powered Questions",
    description:
      "Personalized interview questions generated from your resume and the job description using advanced AI.",
    color: "#7c3aed",
  },
  {
    icon: Mic,
    title: "Voice Interaction",
    description:
      "Human-like voice interviews with real-time speech recognition and natural language responses.",
    color: "#06b6d4",
  },
  {
    icon: Code2,
    title: "Live Coding Rounds",
    description:
      "Built-in code editor for DSA challenges with automated test case evaluation.",
    color: "#10b981",
  },
  {
    icon: BarChart3,
    title: "Detailed Analytics",
    description:
      "Comprehensive scoring across technical, behavioral, and communication skills with improvement plans.",
    color: "#f59e0b",
  },
  {
    icon: Shield,
    title: "FAANG-level Rigor",
    description:
      "Interview styles modeled after top tech companies with adaptive difficulty.",
    color: "#ef4444",
  },
  {
    icon: Zap,
    title: "Instant Feedback",
    description:
      "Real-time evaluation after each answer with specific improvement suggestions.",
    color: "#8b5cf6",
  },
];

const stats = [
  { value: "10K+", label: "Interviews Conducted" },
  { value: "95%", label: "User Satisfaction" },
  { value: "50+", label: "Tech Topics Covered" },
  { value: "4.8★", label: "Average Rating" },
];

export default function LandingPage() {
  return (
    <div style={{ minHeight: "100vh" }}>
      {/* ── Navbar ────────────────────────────────────────────── */}
      <nav
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          zIndex: 50,
          padding: "16px 0",
          backdropFilter: "blur(20px)",
          background: "rgba(10, 10, 15, 0.8)",
          borderBottom: "1px solid var(--border-color)",
        }}
      >
        <div
          style={{
            maxWidth: "1200px",
            margin: "0 auto",
            padding: "0 24px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <Link
            href="/"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              textDecoration: "none",
          }}
          >
            <div
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "10px",
                background: "var(--accent-gradient)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <Brain size={20} color="white" />
            </div>
            <span
              style={{
                fontSize: "1.25rem",
                fontWeight: 700,
                color: "var(--text-primary)",
              }}
            >
              AI Interviewer
            </span>
          </Link>
          <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
            <Link href="/login" className="btn-outline" style={{ padding: "8px 20px", textDecoration: "none" }}>
              Sign In
            </Link>
            <Link href="/register" className="btn-gradient" style={{ padding: "8px 20px", textDecoration: "none" }}>
              Get Started <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      </nav>

      {/* ── Hero ──────────────────────────────────────────────── */}
      <section
        style={{
          paddingTop: "140px",
          paddingBottom: "80px",
          textAlign: "center",
          position: "relative",
        }}
      >
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          style={{ maxWidth: "800px", margin: "0 auto", padding: "0 24px" }}
        >
          <div
            className="badge badge-purple"
            style={{ marginBottom: "24px", display: "inline-flex" }}
          >
            <Sparkles size={14} style={{ marginRight: "6px" }} />
            AI-Powered Interview Practice
          </div>
          <h1
            style={{
              fontSize: "clamp(2.5rem, 5vw, 4rem)",
              fontWeight: 800,
              lineHeight: 1.1,
              marginBottom: "24px",
            }}
          >
            Ace Your Next
            <br />
            <span className="gradient-text">Technical Interview</span>
          </h1>
          <p
            style={{
              fontSize: "1.2rem",
              color: "var(--text-secondary)",
              maxWidth: "600px",
              margin: "0 auto 40px",
              lineHeight: 1.6,
            }}
          >
            Upload your resume and job description. Our AI generates
            personalized questions, conducts realistic interviews, and delivers
            actionable feedback to boost your skills.
          </p>
          <div style={{ display: "flex", gap: "16px", justifyContent: "center" }}>
            <Link href="/register" className="btn-gradient" style={{ fontSize: "1.1rem", padding: "14px 36px", textDecoration: "none" }}>
              Start Free Interview <ArrowRight size={18} />
            </Link>
            <Link href="#features" className="btn-outline" style={{ fontSize: "1.1rem", padding: "14px 36px", textDecoration: "none" }}>
              Learn More
            </Link>
          </div>
        </motion.div>

        {/* Floating orbs */}
        <div
          className="animate-float"
          style={{
            position: "absolute",
            top: "20%",
            left: "10%",
            width: "200px",
            height: "200px",
            borderRadius: "50%",
            background: "radial-gradient(circle, rgba(124,58,237,0.1) 0%, transparent 70%)",
            filter: "blur(40px)",
          }}
        />
        <div
          className="animate-float"
          style={{
            position: "absolute",
            bottom: "10%",
            right: "10%",
            width: "250px",
            height: "250px",
            borderRadius: "50%",
            background: "radial-gradient(circle, rgba(6,182,212,0.1) 0%, transparent 70%)",
            filter: "blur(40px)",
            animationDelay: "3s",
          }}
        />
      </section>

      {/* ── Stats ──────────────────────────────────────────────── */}
      <section style={{ padding: "40px 24px" }}>
        <div
          style={{
            maxWidth: "900px",
            margin: "0 auto",
            display: "grid",
            gridTemplateColumns: "repeat(4, 1fr)",
            gap: "24px",
          }}
        >
          {stats.map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 * i, duration: 0.5 }}
              style={{ textAlign: "center" }}
            >
              <div
                className="gradient-text"
                style={{ fontSize: "2rem", fontWeight: 800 }}
              >
                {stat.value}
              </div>
              <div style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
                {stat.label}
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── Features ──────────────────────────────────────────── */}
      <section id="features" style={{ padding: "80px 24px" }}>
        <div style={{ maxWidth: "1100px", margin: "0 auto" }}>
          <h2
            style={{
              textAlign: "center",
              fontSize: "2.2rem",
              fontWeight: 700,
              marginBottom: "16px",
            }}
          >
            Everything You Need to{" "}
            <span className="gradient-text">Succeed</span>
          </h2>
          <p
            style={{
              textAlign: "center",
              color: "var(--text-secondary)",
              maxWidth: "500px",
              margin: "0 auto 60px",
            }}
          >
            A complete interview preparation platform powered by cutting-edge AI
          </p>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
              gap: "24px",
            }}
          >
            {features.map((feature, i) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 * i, duration: 0.5 }}
                viewport={{ once: true }}
                className="glass-card"
                style={{ padding: "32px" }}
              >
                <div
                  style={{
                    width: "48px",
                    height: "48px",
                    borderRadius: "12px",
                    background: `${feature.color}20`,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    marginBottom: "20px",
                  }}
                >
                  <feature.icon size={24} color={feature.color} />
                </div>
                <h3
                  style={{
                    fontSize: "1.2rem",
                    fontWeight: 600,
                    marginBottom: "8px",
                  }}
                >
                  {feature.title}
                </h3>
                <p style={{ color: "var(--text-secondary)", lineHeight: 1.6 }}>
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ───────────────────────────────────────────────── */}
      <section style={{ padding: "80px 24px" }}>
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="glass-card"
          style={{
            maxWidth: "800px",
            margin: "0 auto",
            padding: "60px 40px",
            textAlign: "center",
            background:
              "linear-gradient(135deg, rgba(124,58,237,0.1) 0%, rgba(6,182,212,0.1) 100%)",
          }}
        >
          <h2 style={{ fontSize: "2rem", fontWeight: 700, marginBottom: "16px" }}>
            Ready to Ace Your Interview?
          </h2>
          <p
            style={{
              color: "var(--text-secondary)",
              marginBottom: "32px",
              maxWidth: "500px",
              margin: "0 auto 32px",
            }}
          >
            Join thousands of candidates who improved their interview skills
            with AI-powered practice sessions.
          </p>
          <Link href="/register" className="btn-gradient" style={{ fontSize: "1.1rem", padding: "16px 40px", textDecoration: "none" }}>
            Start Practicing Now <ArrowRight size={18} />
          </Link>
        </motion.div>
      </section>

      {/* ── Footer ────────────────────────────────────────────── */}
      <footer
        style={{
          padding: "40px 24px",
          borderTop: "1px solid var(--border-color)",
          textAlign: "center",
          color: "var(--text-muted)",
          fontSize: "0.85rem",
        }}
      >
        <p>© 2026 AI Interviewer Platform. Built with ❤️ for developers.</p>
      </footer>
    </div>
  );
}
