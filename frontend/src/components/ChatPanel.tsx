import { useEffect, useRef, useState } from "react";
import Editor from "@monaco-editor/react";
import {
  createConversation,
  fetchConversation,
  saveMessage,
  streamChat,
  streamCodegen,
  streamDebug,
  extractCodeBlock,
  type ChatMessage,
  type CodeLanguage,
} from "../api/client";

type AppMode = "chat" | "generate" | "debug";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

const LANGUAGE_OPTIONS: { value: CodeLanguage; label: string; monaco: string }[] = [
  { value: "python", label: "Python", monaco: "python" },
  { value: "javascript", label: "JavaScript", monaco: "javascript" },
  { value: "typescript", label: "TypeScript", monaco: "typescript" },
  { value: "react", label: "React (JSX)", monaco: "javascript" },
];

const WELCOME: Record<AppMode, string> = {
  chat:
    "Hi! I'm CodeHaven — your offline coding assistant. Ask me about Python, JavaScript, React, or Node.js. Paste code in the editor on the right.",
  generate:
    "Generate mode: describe what you want built and I'll write the code. Pick a language below, then click Generate. Code will appear in the editor automatically.",
  debug:
    "Debug mode: paste your code in the editor and any error message below. I'll explain what's wrong and suggest a fix. Click Apply fix to replace the editor content.",
};

export interface ChatPanelProps {
  mode?: AppMode;
  onModeChange?: (mode: AppMode) => void;
  initialConvId?: string | null;
}

export function ChatPanel({ mode: externalMode, onModeChange, initialConvId }: ChatPanelProps = {}) {
  const [internalMode, setInternalMode] = useState<AppMode>("chat");
  const mode = externalMode ?? internalMode;
  const [activeConvId, setActiveConvId] = useState<string | null>(null);

  const [language, setLanguage] = useState<CodeLanguage>("python");
  const [messages, setMessages] = useState<Message[]>([
    { id: "welcome", role: "assistant", content: WELCOME[mode] },
  ]);
  const [input, setInput] = useState("");
  const [errorInput, setErrorInput] = useState("");
  const [code, setCode] = useState(
    '# Paste code here\n\ndef greet(name):\n    return f"Hello, {name}!"\n'
  );
  const [loading, setLoading] = useState(false);
  const [lastGenerated, setLastGenerated] = useState("");
  const [lastFixed, setLastFixed] = useState("");
  const abortRef = useRef<AbortController | null>(null);

  const monacoLanguage =
    LANGUAGE_OPTIONS.find((o) => o.value === language)?.monaco ?? "python";

  useEffect(() => {
    if (externalMode) {
      setMessages([{ id: "welcome", role: "assistant", content: WELCOME[externalMode] }]);
      setInput("");
      setErrorInput("");
      setLastGenerated("");
      setLastFixed("");
    }
  }, [externalMode]);

  useEffect(() => {
    if (initialConvId) {
      setActiveConvId(initialConvId);
      fetchConversation(initialConvId)
        .then((conv) => {
          if (conv.messages.length > 0) {
            setMessages(
              conv.messages.map((m) => ({
                id: m.id,
                role: m.role as "user" | "assistant",
                content: m.content,
              }))
            );
          }
        })
        .catch(console.error);
    }
  }, [initialConvId]);

  function switchMode(next: AppMode) {
    if (next === mode) return;
    if (onModeChange) {
      onModeChange(next);
    } else {
      setInternalMode(next);
    }
    setMessages([{ id: "welcome", role: "assistant", content: WELCOME[next] }]);
    setInput("");
    setErrorInput("");
    setLastGenerated("");
    setLastFixed("");
  }

  async function sendMessage() {
    if (loading) return;

    if (mode === "debug") {
      if (!code.trim()) return;
      await runDebug();
      return;
    }

    const trimmed = input.trim();
    if (!trimmed) return;

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
    };

    const assistantId = crypto.randomUUID();
    const nextMessages = [...messages, userMsg];
    setMessages([
      ...nextMessages,
      { id: assistantId, role: "assistant", content: "" },
    ]);
    setInput("");
    setLoading(true);
    abortRef.current = new AbortController();

    // Auto-create or resume conversation in SQLite
    let currentConvId = activeConvId;
    if (!currentConvId) {
      currentConvId = crypto.randomUUID();
      setActiveConvId(currentConvId);
      createConversation(trimmed.slice(0, 40), mode, currentConvId).catch(console.error);
    }
    saveMessage(currentConvId, "user", trimmed, undefined, userMsg.id).catch(console.error);

    let fullAssistantResponse = "";

    try {
      if (mode === "chat") {
        const apiMessages: ChatMessage[] = nextMessages.map((m) => ({
          role: m.role,
          content: m.content,
        }));

        if (code.trim()) {
          apiMessages[apiMessages.length - 1].content +=
            `\n\nCode context:\n\`\`\`\n${code}\n\`\`\``;
        }

        await streamChat(
          apiMessages,
          (token) => {
            fullAssistantResponse += token;
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? { ...m, content: m.content + token }
                  : m
              )
            );
          },
          abortRef.current.signal
        );

        if (fullAssistantResponse.trim()) {
          saveMessage(currentConvId, "assistant", fullAssistantResponse, undefined, assistantId).catch(console.error);
        }
      } else {
        let full = "";
        await streamCodegen(
          { prompt: trimmed, language, include_explanation: true },
          (token) => {
            full += token;
            fullAssistantResponse = full;
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId ? { ...m, content: full } : m
              )
            );
          },
          abortRef.current.signal
        );

        const extracted = extractCodeBlock(full);
        setLastGenerated(extracted);
        if (extracted) setCode(extracted);

        if (full.trim()) {
          saveMessage(currentConvId, "assistant", full, undefined, assistantId).catch(console.error);
        }
      }
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Something went wrong.";
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId ? { ...m, content: `Error: ${message}` } : m
        )
      );
    } finally {
      setLoading(false);
      abortRef.current = null;
    }
  }

  async function runDebug() {
    const userContent = errorInput.trim()
      ? `Debug this code (error provided):\n\`\`\`\n${errorInput}\n\`\`\``
      : "Debug the code in the editor.";

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: userContent,
    };

    const assistantId = crypto.randomUUID();
    setMessages((prev) => [
      ...prev,
      userMsg,
      { id: assistantId, role: "assistant", content: "" },
    ]);
    setLoading(true);
    abortRef.current = new AbortController();

    try {
      let full = "";
      await streamDebug(
        {
          code,
          error_message: errorInput.trim() || undefined,
          language,
        },
        (token) => {
          full += token;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, content: full } : m
            )
          );
        },
        abortRef.current.signal
      );

      const fixed = extractCodeBlock(full);
      setLastFixed(fixed);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Something went wrong.";
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId ? { ...m, content: `Error: ${message}` } : m
        )
      );
    } finally {
      setLoading(false);
      abortRef.current = null;
    }
  }

  function stopGeneration() {
    abortRef.current?.abort();
    setLoading(false);
  }

  function insertIntoEditor() {
    if (lastGenerated) setCode(lastGenerated);
  }

  function applyFix() {
    if (lastFixed) setCode(lastFixed);
  }

  const showLanguageSelect = mode === "generate" || mode === "debug";

  return (
    <div className="layout">
      <section className="chat-section">
        <div className="mode-bar">
          <div className="mode-tabs">
            <button
              type="button"
              className={`mode-tab ${mode === "chat" ? "active" : ""}`}
              onClick={() => switchMode("chat")}
            >
              Chat
            </button>
            <button
              type="button"
              className={`mode-tab ${mode === "generate" ? "active" : ""}`}
              onClick={() => switchMode("generate")}
            >
              Generate
            </button>
            <button
              type="button"
              className={`mode-tab ${mode === "debug" ? "active" : ""}`}
              onClick={() => switchMode("debug")}
            >
              Debug
            </button>
          </div>
          {showLanguageSelect && (
            <label className="language-select">
              Language
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value as CodeLanguage)}
                disabled={loading}
              >
                {LANGUAGE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </label>
          )}
        </div>

        <div className="messages">
          {messages.map((m) => (
            <article key={m.id} className={`message ${m.role}`}>
              <div className="message-label">
                {m.role === "user" ? "You" : "CodeHaven"}
              </div>
              <div className="message-body">{m.content || "..."}</div>
            </article>
          ))}
        </div>

        <div className="composer">
          {mode === "debug" && (
            <textarea
              className="error-input"
              value={errorInput}
              onChange={(e) => setErrorInput(e.target.value)}
              placeholder="Paste error or traceback here (optional)..."
              rows={3}
              disabled={loading}
            />
          )}
          {mode !== "debug" && (
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={
                mode === "chat"
                  ? "Ask a coding question..."
                  : "Describe the code to generate (e.g. FastAPI hello-world endpoint)..."
              }
              rows={3}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage();
                }
              }}
            />
          )}
          <div className="composer-actions">
            {mode === "generate" && lastGenerated && !loading && (
              <button
                type="button"
                className="secondary"
                onClick={insertIntoEditor}
              >
                Insert into editor
              </button>
            )}
            {mode === "debug" && lastFixed && !loading && (
              <button type="button" className="secondary" onClick={applyFix}>
                Apply fix
              </button>
            )}
            {loading ? (
              <button type="button" className="secondary" onClick={stopGeneration}>
                Stop
              </button>
            ) : (
              <button
                type="button"
                onClick={sendMessage}
                disabled={mode === "debug" ? !code.trim() : !input.trim()}
              >
                {mode === "chat" ? "Send" : mode === "generate" ? "Generate" : "Analyze"}
              </button>
            )}
          </div>
        </div>
      </section>

      <section className="editor-section">
        <div className="panel-header">
          Code editor
          {showLanguageSelect && (
            <span className="panel-header-meta">{monacoLanguage}</span>
          )}
        </div>
        <Editor
          height="100%"
          language={monacoLanguage}
          theme="vs"
          value={code}
          onChange={(v) => setCode(v ?? "")}
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            wordWrap: "on",
            scrollBeyondLastLine: false,
            automaticLayout: true,
            lineNumbersMinChars: 3,
            padding: { top: 12, bottom: 12 },
            renderLineHighlight: "all",
            scrollbar: {
              verticalScrollbarSize: 10,
              horizontalScrollbarSize: 10,
            },
            overviewRulerBorder: false,
          }}
        />
      </section>
    </div>
  );
}
