"use client";

import { useEffect, useState, useMemo } from "react";
import { useAuthStore } from "@/lib/stores";
import { interviewApi, type InterviewResult } from "@/lib/api";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Legend } from "recharts";
import { Brain, ArrowLeft, Loader2 } from "lucide-react";
import Link from "next/link";
import toast from "react-hot-toast";

type FullResult = InterviewResult & { 
  parsedScores?: Record<string, number>;
  parsedGaps?: string[];
};

export default function AnalyticsPage() {
  const { hydrate } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const [results, setResults] = useState<FullResult[]>([]);

  useEffect(() => { hydrate(); }, [hydrate]);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const response = await interviewApi.list(0, 50);
      const interviews = response.interviews.filter(i => i.status === "scored");
      
      const allResults = await Promise.all(
        interviews.map(async (inv) => {
          try {
            const res = await interviewApi.getResults(inv.id);
            return {
              ...res,
              parsedScores: {
                Technical: res.technical_score || 0,
                Behavioral: res.behavioral_score || 0,
                Communication: res.communication_score || 0,
                "Problem Solving": res.problem_solving_score || 0,
              },
              parsedGaps: JSON.parse(res.skill_gaps || "[]")
            } as FullResult;
          } catch {
            return null;
          }
        })
      );
      
      setResults(allResults.filter(Boolean) as FullResult[]);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Failed to load analytics");
    } finally {
      setLoading(false);
    }
  };

  // Prepare data for the Radar Chart (Averages across all interviews)
  const averageScores = useMemo(() => {
    if (results.length === 0) return [];
    
    const sums = { Technical: 0, Behavioral: 0, Communication: 0, "Problem Solving": 0 };
    results.forEach(r => {
      sums.Technical += (r.technical_score || 0);
      sums.Behavioral += (r.behavioral_score || 0);
      sums.Communication += (r.communication_score || 0);
      sums["Problem Solving"] += (r.problem_solving_score || 0);
    });

    const count = results.length;
    return [
      { subject: "Technical", A: Math.round(sums.Technical / count), fullMark: 100 },
      { subject: "Behavioral", A: Math.round(sums.Behavioral / count), fullMark: 100 },
      { subject: "Communication", A: Math.round(sums.Communication / count), fullMark: 100 },
      { subject: "Problem Solving", A: Math.round(sums["Problem Solving"] / count), fullMark: 100 },
    ];
  }, [results]);

  // Prepare data for the Bar Chart (Trend over time)
  const trendData = useMemo(() => {
    return [...results].reverse().map((r, i) => ({
      name: `Int. ${i + 1}`,
      Overall: r.overall_score || 0,
      Technical: r.technical_score || 0,
    }));
  }, [results]);
  
  // Aggregate prominent skill gaps
  const topGaps = useMemo(() => {
    const counts: Record<string, number> = {};
    results.forEach(r => {
      r.parsedGaps?.forEach((gap: any) => {
        let gapName = "";
        if (typeof gap === "string") {
          gapName = gap;
        } else if (gap && typeof gap === "object") {
          gapName = gap.skill || gap.topic || gap.name || gap.gap || gap.concept || "";
        }
        
        if (gapName && typeof gapName === "string" && gapName.trim() !== "") {
          counts[gapName] = (counts[gapName] || 0) + 1;
        }
      });
    });
    
    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5); // top 5
  }, [results]);

  return (
    <div style={{ padding: "40px 24px", maxWidth: "1200px", margin: "0 auto" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "16px", marginBottom: "32px" }}>
        <Link href="/dashboard" className="glass-card" style={{ padding: "8px", borderRadius: "50%" }}>
          <ArrowLeft size={20} />
        </Link>
        <div>
          <h1 style={{ fontSize: "2rem", fontWeight: 700, margin: 0 }}>Analytics & Skill Heatmap</h1>
          <p style={{ color: "var(--text-secondary)", margin: 0 }}>Visualize your interview performance over time.</p>
        </div>
      </div>

      {loading ? (
        <div style={{ display: "flex", justifyContent: "center", padding: "64px" }}>
          <Loader2 size={32} className="animate-spin" color="var(--accent-primary)" />
        </div>
      ) : results.length === 0 ? (
        <div className="glass-card" style={{ padding: "40px", textAlign: "center" }}>
          <Brain size={48} color="var(--text-muted)" style={{ margin: "0 auto 16px" }} />
          <h3>No Data Yet</h3>
          <p style={{ color: "var(--text-secondary)" }}>Complete your first interview to see the analytics dashboard.</p>
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
          
          {/* Radar Chart Card */}
          <div className="glass-card" style={{ padding: "24px" }}>
            <h3 style={{ marginBottom: "20px" }}>Average Skill Heatmap</h3>
            <div style={{ height: "300px" }}>
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="50%" outerRadius="80%" data={averageScores}>
                  <PolarGrid stroke="rgba(255,255,255,0.1)" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: "var(--text-secondary)", fontSize: 12 }} />
                  <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: "transparent" }} />
                  <Radar name="Average Score" dataKey="A" stroke="var(--accent-primary)" fill="var(--accent-primary)" fillOpacity={0.5} />
                  <Tooltip contentStyle={{ backgroundColor: "rgba(10,10,15,0.9)", borderColor: "rgba(255,255,255,0.1)", borderRadius: "8px" }} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Bar Chart Card */}
          <div className="glass-card" style={{ padding: "24px" }}>
            <h3 style={{ marginBottom: "20px" }}>Score Trend</h3>
            <div style={{ height: "300px" }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="name" tick={{ fill: "var(--text-secondary)", fontSize: 12 }} />
                  <YAxis domain={[0, 100]} tick={{ fill: "var(--text-secondary)", fontSize: 12 }} />
                  <Tooltip contentStyle={{ backgroundColor: "rgba(10,10,15,0.9)", borderColor: "rgba(255,255,255,0.1)", borderRadius: "8px" }} cursor={{ fill: "rgba(255,255,255,0.05)" }} />
                  <Legend />
                  <Bar dataKey="Overall" fill="var(--accent-primary)" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="Technical" fill="var(--accent-secondary)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Top Skill Gaps */}
          <div className="glass-card" style={{ padding: "24px", gridColumn: "1 / -1" }}>
            <h3 style={{ marginBottom: "20px" }}>Most Frequent Skill Gaps</h3>
            {topGaps.length === 0 ? (
              <p style={{ color: "var(--text-secondary)" }}>No recurring skill gaps identified yet. Great job!</p>
            ) : (
              <div style={{ display: "flex", flexWrap: "wrap", gap: "12px" }}>
                {topGaps.map(([gap, count], idx) => (
                  <div key={idx} style={{ 
                    padding: "12px 16px", 
                    background: "rgba(239, 68, 68, 0.1)", 
                    border: "1px solid rgba(239, 68, 68, 0.2)",
                    borderRadius: "8px",
                    display: "flex",
                    alignItems: "center",
                    gap: "8px"
                  }}>
                    <span style={{ color: "var(--text-primary)", fontWeight: 500 }}>{gap}</span>
                    <span style={{ 
                      background: "rgba(239, 68, 68, 0.2)", 
                      color: "var(--error)", 
                      padding: "2px 8px", 
                      borderRadius: "12px", 
                      fontSize: "0.8rem", 
                      fontWeight: 600 
                    }}>{count} occurrences</span>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>
      )}
    </div>
  );
}
