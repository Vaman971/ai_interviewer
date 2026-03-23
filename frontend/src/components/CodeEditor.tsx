"use client";

import { useRef, useState } from "react";
import Editor, { loader } from "@monaco-editor/react";
import type { editor } from "monaco-editor";
import { executionApi } from "@/lib/api";
import { Play, Loader2 } from "lucide-react";

// Fallback to unpkg if jsdelivr is blocked (common cause of the [object Event] load error)
loader.config({
  paths: {
    vs: "https://unpkg.com/monaco-editor@0.44.0/min/vs",
  },
});

interface CodeEditorProps {
  code: string;
  onChange: (value: string | undefined) => void;
  language?: string;
  readOnly?: boolean;
}

export default function CodeEditor({
  code,
  onChange,
  language = "python",
  readOnly = false,
}: CodeEditorProps) {
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);
  const [output, setOutput] = useState<{ stdout: string; stderr: string; compile_output: string | null } | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);

  const handleRunCode = async () => {
    try {
      setIsExecuting(true);
      setOutput(null);
      const res = await executionApi.executeCode(language, code);
      setOutput(res);
    } catch (err: any) {
      setOutput({ stdout: "", stderr: err.message || "Failed to execute code.", compile_output: null });
    } finally {
      setIsExecuting(false);
    }
  };

  const handleEditorWillMount = (monaco: any) => {
    monaco.editor.defineTheme("interviewDark", {
      base: "vs-dark",
      inherit: true,
      rules: [],
      colors: {
        "editor.background": "#0f172a", // Tailwind slate-900
        "editor.lineHighlightBackground": "#1e293b", // Tailwind slate-800
      },
    });
  };

  const handleEditorDidMount = (editor: editor.IStandaloneCodeEditor) => {
    editorRef.current = editor;
  };

  return (
    <div className="flex flex-col h-full w-full rounded-lg overflow-hidden border border-slate-700 shadow-sm bg-slate-900">
      <div className="flex justify-between items-center px-4 py-2 border-b border-slate-700 bg-slate-800">
        <span className="text-sm text-slate-400 font-medium capitalize">{language}</span>
        <button
          onClick={handleRunCode}
          disabled={isExecuting || readOnly}
          className="flex items-center gap-2 px-3 py-1.5 text-sm font-semibold rounded-md bg-emerald-600 hover:bg-emerald-500 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isExecuting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
          Run Code
        </button>
      </div>

      <div className="flex-1 relative">
        <Editor
          height="100%"
          defaultLanguage={language}
          language={language}
          value={code}
          onChange={onChange}
          beforeMount={handleEditorWillMount}
          onMount={handleEditorDidMount}
          theme="interviewDark"
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            wordWrap: "on",
            readOnly: readOnly,
            padding: { top: 16 },
            scrollBeyondLastLine: false,
            automaticLayout: true,
          }}
        />
      </div>

      {output && (
        <div className="h-[30%] min-h-[150px] border-t border-slate-700 bg-black p-4 overflow-y-auto font-mono text-sm">
          <h3 className="text-slate-400 mb-2 font-semibold">Terminal Output</h3>
          {output.compile_output && (
            <div className="text-orange-400 whitespace-pre-wrap mb-2">{output.compile_output}</div>
          )}
          {output.stderr && <div className="text-red-400 whitespace-pre-wrap mb-2">{output.stderr}</div>}
          {output.stdout && <div className="text-emerald-400 whitespace-pre-wrap">{output.stdout}</div>}
          {!output.stderr && !output.stdout && !output.compile_output && (
            <div className="text-slate-500 italic">Program finished successfully with no output.</div>
          )}
        </div>
      )}
    </div>
  );
}
