"use client";

import { useState, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  Brain,
  Send,
  ArrowLeft,
  Clock,
  CheckCircle2,
  Loader2,
  MessageSquare,
  ChevronRight,
  Award,
  Mic,
  MicOff,
  Volume2,
  GripHorizontal,
} from "lucide-react";
import toast from "react-hot-toast";
import { interviewApi, type Question, type AnswerEvaluation } from "@/lib/api";
import { useAuthStore } from "@/lib/stores";

interface ChatMessage {
  role: "interviewer" | "candidate";
  content: string;
  evaluation?: AnswerEvaluation;
  questionType?: string;
  difficulty?: string;
}

import dynamic from "next/dynamic";

const CodeEditor = dynamic(() => import("@/components/CodeEditor"), { ssr: false });

/**
 * Primary Interview Orchestration Component
 * 
 * This highly complex component manages the entire real-time interview lifecycle:
 * - Mounts the `CodeEditor` dynamically securely when a DSA question arises.
 * - Records, chunks, and uploads user voice to STT backend via `MediaRecorder`.
 * - Aggregates audio streams into the continuous `playQuestionAudio` pipeline.
 * - Controls the floating `Audio Visualizer` animation based on TTS payload arrival.
 * - Implements anti-cheat tracking via explicit window/blur event listeners.
 * 
 * @returns {JSX.Element} The fully rendered Interview Room UI.
 */
export default function InterviewRoomPage() {
  const params = useParams();
  const router = useRouter();
  const interviewId = params.id as string;

  const { hydrate } = useAuthStore();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);
  const [answer, setAnswer] = useState("");
  const [codeContent, setCodeContent] = useState("# Write your solution here...\n");
  const [loading, setLoading] = useState(false);
  const [fetchingQuestion, setFetchingQuestion] = useState(true);
  const [startTime, setStartTime] = useState<number>(Date.now());
  const [isComplete, setIsComplete] = useState(false);
  const [completing, setCompleting] = useState(false);
  const [confirmExit, setConfirmExit] = useState(false);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  
  const chatEndRef = useRef<HTMLDivElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<BlobPart[]>([]);

  // Audio Visualizer State
  const [isAudioPlaying, setIsAudioPlaying] = useState(false);

  useEffect(() => { hydrate(); }, [hydrate]);

  // Cheat detection: monitor tab switches and window blur events
  useEffect(() => {
    if (isComplete) return;

    const handleVisibilityChange = () => {
      if (document.hidden) {
        setWarnings(prev => [...prev, `Tab switched away at ${new Date().toLocaleTimeString()}`]);
        toast.error("Warning: Navigating away from the interview tab is recorded.", {
          icon: '⚠️',
        });
      }
    };

    const handleBlur = () => {
      setWarnings(prev => [...prev, `Window lost focus at ${new Date().toLocaleTimeString()}`]);
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    window.addEventListener("blur", handleBlur);

    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      window.removeEventListener("blur", handleBlur);
    };
  }, [isComplete]);


  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  /**
   * Converts textual AI responses into a raw audio blob via the TTS API,
   * instantiates an `Audio` object, handles playback promises, and orchestrates the Visualizer UI animations.
   * 
   * @param {string} text - The text string to synthesize.
   * @returns {Promise<void>} Resolves when the audio natively finishes playing via `audio.onended`.
   */
  const playQuestionAudio = async (text: string): Promise<void> => {
    return new Promise(async (resolve) => {
      try {
        setIsAudioPlaying(true);
        const token = localStorage.getItem("access_token");
        
        const url = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/media/tts?text=${encodeURIComponent(text)}`;
        const res = await fetch(url, {
          method: "POST",
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
        if (!res.ok) {
          setIsAudioPlaying(false);
          resolve();
          return;
        }
        const blob = await res.blob();
        const audioUrl = URL.createObjectURL(blob);
        const audio = new Audio(audioUrl);
        audio.onended = () => { setIsAudioPlaying(false); resolve(); };
        audio.onerror = () => { setIsAudioPlaying(false); resolve(); };
        await audio.play().catch((err) => {
          console.error("Autoplay prevented:", err);
          setIsAudioPlaying(false);
          resolve();
        });
      } catch (err) {
        console.error("Failed to play TTS audio", err);
        setIsAudioPlaying(false);
        resolve();
      }
    });
  };



  /**
   * Fetches the next question from the backend and triggers the native TTS engine.
   * 
   * Reads the current index from the DB session and pushes the question text
   * to the chat UI. Conditionally invokes `playQuestionAudio` based on parameter.
   * 
   * @param {boolean} playAudio - Whether to autonomously trigger the voice visualizer for this question.
   */
  const fetchInitialQuestion = async (playAudio: boolean = true) => {
    setFetchingQuestion(true);
    try {
      const q = await interviewApi.getNextQuestion(interviewId);
      setCurrentQuestion(q);
      const isDsa = q.question_type === "dsa";
      
      const newQuestionContent = q.question_text + (isDsa ? "\n\n(Please write your solution in the code editor and explain your approach in the chat)" : "");
      setMessages((prev) => {
        if (prev.length > 0 && prev[prev.length - 1].role === "interviewer" 
            && prev[prev.length - 1].content === newQuestionContent) {
          return prev;
        }
        return [
          ...prev,
          {
            role: "interviewer",
            content: newQuestionContent,
            questionType: q.question_type,
            difficulty: q.difficulty,
          },
        ];
      });
      setStartTime(Date.now());
      if (isDsa) {
        setCodeContent("# Write your solution here...\n");
      }
      
      // Auto-play the TTS for the new question to simulate a real conversation
      if (playAudio && q.question_text) {
        playQuestionAudio(q.question_text);
      }
      return q;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "";
      if (message.includes("All questions")) {
        setIsComplete(true);
      } else {
        toast.error(message || "Failed to load question");
      }
      return null;
    } finally {
      setFetchingQuestion(false);
    }
  };

  useEffect(() => {
    fetchInitialQuestion();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSubmit = async () => {
    // For DSA questions, we submit both chat answer and code
    const isDsa = currentQuestion?.question_type === "dsa";
    const finalAnswer = isDsa ? `[Code Submission]:\n\`\`\`python\n${codeContent}\n\`\`\`\n\n[Explanation]:\n${answer}` : answer;

    if (!finalAnswer.trim() || !currentQuestion) return;

    const timeTaken = (Date.now() - startTime) / 1000;

    setMessages((prev) => [...prev, { role: "candidate", content: finalAnswer }]);
    setAnswer("");
    setLoading(true);

    try {
      const evaluation = await interviewApi.submitAnswer(
        interviewId,
        currentQuestion.question_index,
        finalAnswer,
        timeTaken,
        warnings // Send gathered warnings to backend
      );
      
      // Clear warnings for the next question
      setWarnings([]);

      let responseToSpeak = "";

      // Show evaluation box on the candidate's own message
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          ...updated[updated.length - 1],
          evaluation,
        };
        
        // --- NEW: Conversational transition ---
        // Inject an immediate interviewer response that acknowledges the answer
        const interviewerResponseStr = `${evaluation.encouragement ? evaluation.encouragement + "\n\n" : ""}${evaluation.feedback}`;
        responseToSpeak = interviewerResponseStr;
        
        return [
          ...updated,
          {
            role: "interviewer" as const,
            content: interviewerResponseStr,
          }
        ];
      });

      // Check if more questions
      if (currentQuestion.question_index + 1 >= currentQuestion.total_questions) {
        setIsComplete(true);
        await playQuestionAudio(responseToSpeak);
      } else {
        // Fetch next question seamlessly but silently (playAudio=false) 
        // and combine the text so the Avatar/TTS says it all at once without overlapping!
        const nextQ = await fetchInitialQuestion(false);
        if (nextQ) {
          const combinedText = `${responseToSpeak} Now for your next question. ${nextQ.question_text}`;
          await playQuestionAudio(combinedText);
        } else {
          await playQuestionAudio(responseToSpeak);
        }
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Submit failed";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const handleComplete = async () => {
    setCompleting(true);
    try {
      await interviewApi.complete(interviewId);
      toast.success("Interview completed! Generating results...");
      router.push(`/interview/${interviewId}/results`);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to complete";
      toast.error(message);
    } finally {
      setCompleting(false);
    }
  };

  // Voice Recording Logic (WebRTC STT)
  const toggleRecording = async () => {
    if (isRecording) {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
        mediaRecorderRef.current.stop();
        setIsRecording(false);
      }
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/wav" });
        stream.getTracks().forEach((track) => track.stop());
        
        // Upload audioBlob to STT endpoint
        await transcribeAudio(audioBlob);
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      toast.error("Microphone access denied or unavailable.");
    }
  };

  const transcribeAudio = async (audioBlob: Blob) => {
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("file", audioBlob, "recording.wav");
      
      const token = localStorage.getItem("access_token");
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/media/stt`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      });
      
      if (!res.ok) throw new Error("STT failed");
      
      const data = await res.json();
      const transcribedText = data.transcript || "";
      
      if (transcribedText.trim()) {
        const newAnswer = answer ? answer + " " + transcribedText : transcribedText;
        setAnswer(newAnswer);
        toast.success("Voice transcribed successfully. Submitting...");
        
        // Auto-submit the voice answer to make it feel like a live conversation!
        // We use setTimeout to ensure React state has updated before submitting.
        setTimeout(() => {
            const submitBtn = document.getElementById("submit-answer-btn");
            if (submitBtn) submitBtn.click();
        }, 500);
      } else {
        toast.error("Could not hear anything clearly. Try again.");
      }
    } catch (err) {
      toast.error("Failed to transcribe audio");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const typeColors: Record<string, string> = {
    behavioral: "#f59e0b",
    technical: "#7c3aed",
    dsa: "#10b981",
    system_design: "#06b6d4",
    resume_deep_dive: "#8b5cf6",
  };

  const isDsaActive = currentQuestion?.question_type === "dsa" && !isComplete;

  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      {/* Top Bar */}
      <div style={{
        padding: "12px 24px",
        borderBottom: "1px solid var(--border-color)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        background: "rgba(10, 10, 15, 0.9)",
        backdropFilter: "blur(20px)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <Link href="/dashboard" style={{ color: "var(--text-muted)", display: "flex" }}>
            <ArrowLeft size={18} />
          </Link>
          <Brain size={20} color="var(--accent-primary)" />
          <span style={{ fontWeight: 600 }}>Interview Session</span>
          {currentQuestion && (
            <span className="badge badge-purple">
              Q{(currentQuestion.question_index + 1)} / {currentQuestion.total_questions}
            </span>
          )}
        </div>
        {isComplete ? (
          <button onClick={handleComplete} className="btn-gradient" disabled={completing} style={{ padding: "8px 20px" }}>
            {completing ? <Loader2 size={16} className="animate-spin" /> : <><Award size={16} /> View Results</>}
          </button>
        ) : confirmExit ? (
          <div style={{ display: "flex", gap: "8px" }}>
            <button onClick={() => setConfirmExit(false)} className="btn-outline" style={{ padding: "6px 12px", border: "none" }}>
              Cancel
            </button>
            <button onClick={handleComplete} disabled={completing} className="btn-solid" style={{ padding: "6px 16px", backgroundColor: "var(--error)", color: "white" }}>
              {completing ? <Loader2 size={16} className="animate-spin" /> : "Confirm Exit"}
            </button>
          </div>
        ) : (
          <button onClick={() => setConfirmExit(true)} className="btn-outline" style={{ padding: "6px 16px", borderColor: "var(--error)", color: "var(--error)" }}>
            Exit Interview
          </button>
        )}
      </div>

      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        {/* Chat Area */}
        <div style={{ 
          flex: isDsaActive ? "0 0 45%" : 1, 
          display: "flex", 
          flexDirection: "column", 
          borderRight: isDsaActive ? "1px solid var(--border-color)" : "none",
          transition: "flex 0.3s ease",
          height: "100%"
        }}>
          {/* Pinned Question & Avatar Panel */}
          <div style={{ padding: "24px 24px 0", maxWidth: isDsaActive ? "100%" : "800px", width: "100%", margin: isDsaActive ? "0" : "0 auto", flexShrink: 0 }}>
            {!isComplete && currentQuestion && (
              <motion.div 
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                style={{ padding: "16px 20px", marginBottom: "16px", borderRadius: "12px", background: "rgba(124, 58, 237, 0.05)", display: "flex", gap: "16px", alignItems: "center", border: "1px solid rgba(124, 58, 237, 0.2)", boxShadow: "0 4px 12px rgba(0,0,0,0.1)" }}
              >
                <div style={{ width: "60px", height: "60px", borderRadius: "50%", background: "var(--accent-gradient)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, boxShadow: "0 0 15px rgba(124, 58, 237, 0.4)" }}>
                  <Brain size={30} color="white" />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                     <h3 style={{ fontSize: "0.8rem", color: "var(--accent-primary)", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em" }}>Current Question</h3>
                  </div>
                  <p style={{ fontSize: "1rem", fontWeight: 500, lineHeight: 1.5 }}>{currentQuestion.question_text}</p>
                </div>
              </motion.div>
            )}

          </div>

          {/* Draggable Floating Audio Visualizer Panel */}
          {!isComplete && (
             <motion.div
                drag
                dragMomentum={false}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                style={{ 
                   position: "fixed",
                   top: "80px",
                   right: "40px",
                   zIndex: 100,
                   width: "260px", 
                   height: "180px",
                   borderRadius: "16px", 
                   overflow: "hidden", 
                   background: "rgba(15, 10, 25, 0.85)", 
                   backdropFilter: "blur(12px)",
                   border: "1px solid rgba(124, 58, 237, 0.4)", 
                   boxShadow: "0 15px 40px rgba(0,0,0,0.5), 0 0 20px rgba(124,58,237,0.15)",
                   display: "flex", 
                   alignItems: "center", 
                   justifyContent: "center",
                   cursor: "grab"
                }}
                whileDrag={{ cursor: "grabbing", scale: 1.05, boxShadow: "0 25px 50px rgba(0,0,0,0.6)" }}
             >
                {/* Drag Handle Indicator */}
                <div style={{ position: "absolute", top: "8px", width: "100%", display: "flex", justifyContent: "center", opacity: 0.5 }}>
                  <GripHorizontal size={20} color="var(--text-muted)" />
                </div>

                <div style={{ position: "relative", width: "100px", height: "100px", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  {/* Glowing outer rings when talking */}
                  <AnimatePresence>
                    {isAudioPlaying && (
                      <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        style={{ position: "absolute", inset: -40, display: "flex", alignItems: "center", justifyContent: "center" }}
                      >
                        <motion.div
                          animate={{ scale: [1, 1.4, 1], opacity: [0.4, 0, 0.4] }}
                          transition={{ repeat: Infinity, duration: 1.5, ease: "easeInOut" }}
                          style={{ position: "absolute", inset: 20, borderRadius: "50%", border: "2px solid var(--accent-primary)" }}
                        />
                        <motion.div
                          animate={{ scale: [1, 1.7, 1], opacity: [0.2, 0, 0.2] }}
                          transition={{ repeat: Infinity, duration: 2, ease: "easeInOut", delay: 0.2 }}
                          style={{ position: "absolute", inset: 0, borderRadius: "50%", border: "1px solid var(--accent-secondary)" }}
                        />
                        <motion.div
                          animate={{ scale: [1, 1.2, 1], opacity: [0.8, 0.3, 0.8] }}
                          transition={{ repeat: Infinity, duration: 1, ease: "easeInOut" }}
                          style={{ position: "absolute", inset: 30, borderRadius: "50%", background: "var(--accent-primary)", filter: "blur(15px)" }}
                        />
                      </motion.div>
                    )}
                  </AnimatePresence>
                  
                  {/* Core Brain Icon */}
                  <div style={{ position: "relative", zIndex: 10, width: "60px", height: "60px", borderRadius: "50%", background: isAudioPlaying ? "var(--accent-gradient)" : "rgba(124, 58, 237, 0.15)", display: "flex", alignItems: "center", justifyContent: "center", border: "2px solid rgba(255,255,255,0.1)", transition: "background 0.3s ease" }}>
                    <Brain size={32} color={isAudioPlaying ? "white" : "var(--accent-primary)"} />
                  </div>
                </div>
                
                <div style={{ position: "absolute", bottom: "12px", width: "100%", display: "flex", justifyContent: "center" }}>
                   <span className="badge badge-purple" style={{ backdropFilter: "blur(10px)", background: "rgba(124, 58, 237, 0.3)", fontSize: "0.65rem", padding: "4px 10px", border: "1px solid rgba(124, 58, 237, 0.5)"}}>
                      <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: isAudioPlaying ? "#10b981" : "#6b7280", marginRight: "6px", animation: isAudioPlaying ? "pulse 1s infinite" : "none" }} />
                      {isAudioPlaying ? "AI is Speaking..." : "AI is Listening..."}
                   </span>
                </div>
             </motion.div>
          )}

          {/* Scrolling Chat Area */}
          <div style={{ flex: 1, overflowY: "auto", padding: "0 24px 24px", maxWidth: isDsaActive ? "100%" : "800px", width: "100%", margin: isDsaActive ? "0" : "0 auto" }}>
            
            <AnimatePresence>
              {messages.map((msg, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                  style={{
                    marginBottom: "20px",
                    display: "flex",
                    justifyContent: msg.role === "candidate" ? "flex-end" : "flex-start",
                  }}
                >
                  <div style={{ maxWidth: "85%" }}>
                    {/* Interviewer message */}
                    {msg.role === "interviewer" && (
                      <div>
                        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
                          <div style={{ width: "28px", height: "28px", borderRadius: "50%", background: "var(--accent-gradient)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                            <Brain size={14} color="white" />
                          </div>
                          <span style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--text-secondary)" }}>Interviewer</span>
                          {msg.questionType && (
                            <span className="badge" style={{ background: `${typeColors[msg.questionType] || "#7c3aed"}20`, color: typeColors[msg.questionType] || "#7c3aed", border: `1px solid ${typeColors[msg.questionType] || "#7c3aed"}40`, fontSize: "0.65rem" }}>
                              {msg.questionType.replace("_", " ")}
                            </span>
                          )}
                        </div>
                        <div className="glass-card" style={{ padding: "16px 20px", lineHeight: 1.7, whiteSpace: "pre-wrap" }}>
                          {msg.content}
                        </div>
                      </div>
                    )}

                    {/* Candidate message */}
                    {msg.role === "candidate" && (
                      <div>
                        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px", justifyContent: "flex-end" }}>
                          <span style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--text-secondary)" }}>You</span>
                        </div>
                        <div style={{
                          padding: "16px 20px",
                          borderRadius: "var(--radius)",
                          background: "rgba(124, 58, 237, 0.15)",
                          border: "1px solid rgba(124, 58, 237, 0.3)",
                          lineHeight: 1.7,
                          whiteSpace: "pre-wrap",
                        }}>
                          {msg.content}
                        </div>

                        {/* Evaluation */}
                        {msg.evaluation && (
                          <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: "auto" }}
                            style={{
                              marginTop: "8px",
                              padding: "12px 16px",
                              borderRadius: "var(--radius-sm)",
                              background: "rgba(16, 185, 129, 0.08)",
                              border: "1px solid rgba(16, 185, 129, 0.2)",
                              fontSize: "0.85rem",
                            }}
                          >
                            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                              <CheckCircle2 size={14} color="var(--success)" />
                              <span style={{ fontWeight: 600, color: "var(--success)" }}>
                                Score: {msg.evaluation.score}/10
                              </span>
                            </div>
                            <p style={{ color: "var(--text-secondary)" }}>{msg.evaluation.feedback}</p>
                          </motion.div>
                        )}
                      </div>
                    )}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>

            {fetchingQuestion && !isComplete && (
              <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--text-muted)" }}>
                <Loader2 size={16} className="animate-spin" />
                <span style={{ fontSize: "0.85rem" }}>Preparing next question...</span>
              </div>
            )}

            {isComplete && messages.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass-card"
                style={{ padding: "32px", textAlign: "center", background: "rgba(124, 58, 237, 0.08)" }}
              >
                <Award size={40} color="var(--accent-primary)" style={{ marginBottom: "12px" }} />
                <h3 style={{ fontSize: "1.2rem", fontWeight: 700, marginBottom: "8px" }}>Interview Complete! 🎉</h3>
                <p style={{ color: "var(--text-secondary)", marginBottom: "20px" }}>
                  Great job! Click below to generate your detailed results and feedback.
                </p>
                <button onClick={handleComplete} className="btn-gradient" disabled={completing}>
                  {completing ? <Loader2 size={18} className="animate-spin" /> : <>Generate Results <ChevronRight size={16} /></>}
                </button>
              </motion.div>
            )}

            <div ref={chatEndRef} />
          </div>

          {/* Input Area */}
          {!isComplete && (
            <div style={{
              padding: "16px 24px",
              borderTop: "1px solid var(--border-color)",
              background: "rgba(10, 10, 15, 0.9)",
              backdropFilter: "blur(20px)",
            }}>
              <div style={{ maxWidth: "800px", margin: "0 auto", display: "flex", gap: "12px", flexDirection: "column" }}>
                <textarea
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={isDsaActive ? "Explain your approach here, and write code on the right..." : "Type your answer... (Enter to send, Shift+Enter for new line)"}
                  className="textarea-field"
                  style={{ minHeight: "60px", maxHeight: "200px", resize: "none" }}
                  disabled={loading || fetchingQuestion}
                />
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <button
                    onClick={toggleRecording}
                    className="btn-outline"
                    disabled={loading || fetchingQuestion}
                    style={{
                      borderRadius: "50%",
                      width: "48px",
                      height: "48px",
                      padding: 0,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      color: isRecording ? "white" : "var(--accent-primary)",
                      background: isRecording ? "var(--error)" : "transparent",
                      borderColor: isRecording ? "var(--error)" : "var(--accent-primary)",
                      animation: isRecording ? "pulse 1.5s infinite" : "none",
                    }}
                    title={isRecording ? "Stop Recording & Send" : "Use Voice to Answer"}
                  >
                    {isRecording ? <MicOff size={20} /> : <Mic size={20} />}
                  </button>

                  <button
                    id="submit-answer-btn"
                    onClick={handleSubmit}
                    className="btn-gradient"
                    disabled={!answer.trim() || loading || fetchingQuestion}
                    style={{ padding: "10px 24px" }}
                  >
                    {loading ? <Loader2 size={18} className="animate-spin" /> : <><Send size={18} style={{marginRight: "8px"}} /> Submit Answer</>}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Code Editor Area */}
        {isDsaActive && (
          <motion.div 
            initial={{ opacity: 0, width: 0 }}
            animate={{ opacity: 1, width: "55%" }}
            style={{ padding: "16px", display: "flex", flexDirection: "column" }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "12px", alignItems: "center" }}>
              <h3 style={{ fontSize: "1rem", fontWeight: 600 }}>Code Editor</h3>
              <span className="badge badge-purple" style={{ fontSize: "0.75rem" }}>Python 3.11</span>
            </div>
            <div style={{ flex: 1, minHeight: 0 }}>
              <CodeEditor 
                code={codeContent} 
                onChange={(val) => setCodeContent(val || "")} 
                language="python"
              />
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}

