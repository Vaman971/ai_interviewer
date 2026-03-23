"use client";

import { useState, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Brain,
  Upload,
  FileText,
  Briefcase,
  ArrowRight,
  ArrowLeft,
  Loader2,
  Check,
  Settings,
} from "lucide-react";
import toast from "react-hot-toast";
import { useDropzone } from "react-dropzone";
import { interviewApi } from "@/lib/api";
import { useAuthStore, useInterviewStore } from "@/lib/stores";

export default function InterviewSetupPage() {
  const router = useRouter();
  const { isAuthenticated, hydrate } = useAuthStore();
  const { setCurrentInterview } = useInterviewStore();

  const [step, setStep] = useState(1);
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [jdText, setJdText] = useState("");
  const [interviewType, setInterviewType] = useState("full");
  const [personality, setPersonality] = useState("professional");
  const [difficulty, setDifficulty] = useState("medium");
  const [loading, setLoading] = useState(false);

  useEffect(() => { hydrate(); }, [hydrate]);
  useEffect(() => {
    if (!localStorage.getItem("access_token")) router.push("/login");
  }, [router]);

  const onDrop = useCallback((files: File[]) => {
    if (files.length > 0) setResumeFile(files[0]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"], "text/plain": [".txt"] },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024,
  });

  const interviewTypes = [
    { value: "full", label: "Full Interview", desc: "Behavioral + Technical + DSA" },
    { value: "technical", label: "Technical Only", desc: "Deep technical questions" },
    { value: "behavioral", label: "Behavioral Only", desc: "STAR-format questions" },
    { value: "dsa", label: "DSA Only", desc: "Coding problems" },
  ];

  const personalities = [
    { value: "professional", label: "Professional", emoji: "👔" },
    { value: "friendly", label: "Friendly", emoji: "😊" },
    { value: "strict", label: "Strict", emoji: "🎯" },
    { value: "faang", label: "FAANG Style", emoji: "🏢" },
  ];

  const difficulties = [
    { value: "easy", label: "Easy", color: "#10b981" },
    { value: "medium", label: "Medium", color: "#f59e0b" },
    { value: "hard", label: "Hard", color: "#ef4444" },
  ];

  const handleStart = async () => {
    if (!resumeFile) { toast.error("Please upload your resume"); return; }
    if (!jdText.trim()) { toast.error("Please provide a job description"); return; }

    setLoading(true);
    try {
      // 1. Create interview
      const interview = await interviewApi.create({
        interview_type: interviewType,
        personality_mode: personality,
        difficulty_level: difficulty,
      });

      // 2. Upload resume
      await interviewApi.uploadResume(interview.id, resumeFile);

      // 3. Upload JD
      await interviewApi.uploadJD(interview.id, jdText);

      // 4. Start interview (triggers AI pipeline)
      toast.loading("AI is analyzing your profile...", { id: "prep" });
      await interviewApi.start(interview.id);
      toast.success("Interview is ready!", { id: "prep" });

      setCurrentInterview(interview.id);
      router.push(`/interview/${interview.id}`);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to start interview";
      toast.error(message, { id: "prep" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh" }}>
      {/* Nav */}
      <nav style={{ padding: "16px 24px", borderBottom: "1px solid var(--border-color)", display: "flex", alignItems: "center", gap: "16px" }}>
        <Link href="/dashboard" style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--text-secondary)", textDecoration: "none", fontSize: "0.9rem" }}>
          <ArrowLeft size={16} /> Dashboard
        </Link>
        <span style={{ color: "var(--text-muted)" }}>/</span>
        <span style={{ color: "var(--text-primary)", fontWeight: 600 }}>New Interview</span>
      </nav>

      <div style={{ maxWidth: "700px", margin: "40px auto", padding: "0 24px" }}>
        {/* Progress */}
        <div style={{ display: "flex", gap: "8px", marginBottom: "40px" }}>
          {[1, 2, 3].map((s) => (
            <div key={s} style={{ flex: 1, height: "4px", borderRadius: "2px", background: s <= step ? "var(--accent-primary)" : "var(--border-color)", transition: "all 0.3s" }} />
          ))}
        </div>

        {/* Step 1: Upload Resume */}
        {step === 1 && (
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}>
            <h2 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "8px" }}>
              <Upload size={24} style={{ marginRight: "8px", verticalAlign: "middle" }} />
              Upload Your Resume
            </h2>
            <p style={{ color: "var(--text-secondary)", marginBottom: "32px" }}>
              We&apos;ll analyze your skills, experience, and projects to personalize the interview
            </p>

            <div
              {...getRootProps()}
              className="glass-card"
              style={{
                padding: "60px 40px",
                textAlign: "center",
                cursor: "pointer",
                borderStyle: "dashed",
                borderWidth: "2px",
                borderColor: isDragActive ? "var(--accent-primary)" : "var(--border-color)",
                background: isDragActive ? "rgba(124, 58, 237, 0.05)" : undefined,
              }}
            >
              <input {...getInputProps()} />
              {resumeFile ? (
                <>
                  <Check size={40} color="var(--success)" style={{ marginBottom: "12px" }} />
                  <p style={{ fontWeight: 600, marginBottom: "4px" }}>{resumeFile.name}</p>
                  <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
                    {(resumeFile.size / 1024).toFixed(1)} KB · Click to change
                  </p>
                </>
              ) : (
                <>
                  <FileText size={40} color="var(--text-muted)" style={{ marginBottom: "12px" }} />
                  <p style={{ fontWeight: 600, marginBottom: "4px" }}>Drop your resume here</p>
                  <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
                    PDF or TXT · Max 10MB
                  </p>
                </>
              )}
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "32px" }}>
              <button onClick={() => resumeFile ? setStep(2) : toast.error("Upload a resume first")} className="btn-gradient">
                Continue <ArrowRight size={16} />
              </button>
            </div>
          </motion.div>
        )}

        {/* Step 2: Job Description */}
        {step === 2 && (
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}>
            <h2 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "8px" }}>
              <Briefcase size={24} style={{ marginRight: "8px", verticalAlign: "middle" }} />
              Job Description
            </h2>
            <p style={{ color: "var(--text-secondary)", marginBottom: "32px" }}>
              Paste the job description to generate targeted interview questions
            </p>

            <textarea
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              className="textarea-field"
              placeholder="Paste the full job description here..."
              style={{ minHeight: "250px" }}
            />

            <div style={{ display: "flex", justifyContent: "space-between", marginTop: "32px" }}>
              <button onClick={() => setStep(1)} className="btn-outline">
                <ArrowLeft size={16} /> Back
              </button>
              <button onClick={() => jdText.trim() ? setStep(3) : toast.error("Enter a job description")} className="btn-gradient">
                Continue <ArrowRight size={16} />
              </button>
            </div>
          </motion.div>
        )}

        {/* Step 3: Settings */}
        {step === 3 && (
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}>
            <h2 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "8px" }}>
              <Settings size={24} style={{ marginRight: "8px", verticalAlign: "middle" }} />
              Interview Settings
            </h2>
            <p style={{ color: "var(--text-secondary)", marginBottom: "32px" }}>
              Customize your interview experience
            </p>

            {/* Type */}
            <h3 style={{ fontSize: "1rem", fontWeight: 600, marginBottom: "12px" }}>Interview Type</h3>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "12px", marginBottom: "28px" }}>
              {interviewTypes.map((t) => (
                <div
                  key={t.value}
                  onClick={() => setInterviewType(t.value)}
                  className="glass-card"
                  style={{
                    padding: "16px",
                    cursor: "pointer",
                    borderColor: interviewType === t.value ? "var(--accent-primary)" : undefined,
                    background: interviewType === t.value ? "rgba(124, 58, 237, 0.1)" : undefined,
                  }}
                >
                  <div style={{ fontWeight: 600, fontSize: "0.95rem" }}>{t.label}</div>
                  <div style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>{t.desc}</div>
                </div>
              ))}
            </div>

            {/* Personality */}
            <h3 style={{ fontSize: "1rem", fontWeight: 600, marginBottom: "12px" }}>Interviewer Style</h3>
            <div style={{ display: "flex", gap: "12px", marginBottom: "28px", flexWrap: "wrap" }}>
              {personalities.map((p) => (
                <div
                  key={p.value}
                  onClick={() => setPersonality(p.value)}
                  className="glass-card"
                  style={{
                    padding: "12px 20px",
                    cursor: "pointer",
                    borderColor: personality === p.value ? "var(--accent-primary)" : undefined,
                    background: personality === p.value ? "rgba(124, 58, 237, 0.1)" : undefined,
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                  }}
                >
                  <span>{p.emoji}</span>
                  <span style={{ fontWeight: 600, fontSize: "0.9rem" }}>{p.label}</span>
                </div>
              ))}
            </div>

            {/* Difficulty */}
            <h3 style={{ fontSize: "1rem", fontWeight: 600, marginBottom: "12px" }}>Difficulty</h3>
            <div style={{ display: "flex", gap: "12px", marginBottom: "32px" }}>
              {difficulties.map((d) => (
                <div
                  key={d.value}
                  onClick={() => setDifficulty(d.value)}
                  className="glass-card"
                  style={{
                    padding: "12px 24px",
                    cursor: "pointer",
                    borderColor: difficulty === d.value ? d.color : undefined,
                    background: difficulty === d.value ? `${d.color}15` : undefined,
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                  }}
                >
                  <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: d.color }} />
                  <span style={{ fontWeight: 600, fontSize: "0.9rem" }}>{d.label}</span>
                </div>
              ))}
            </div>

            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <button onClick={() => setStep(2)} className="btn-outline">
                <ArrowLeft size={16} /> Back
              </button>
              <button onClick={handleStart} className="btn-gradient" disabled={loading}>
                {loading ? <Loader2 size={18} className="animate-spin" /> : <>Start Interview <ArrowRight size={16} /></>}
              </button>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}
