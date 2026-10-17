import { useState } from "react";
import { StatusBar } from "./components/StatusBar";
import { ChatPanel } from "./components/ChatPanel";
import { NotesPanel } from "./components/NotesPanel";
import { ExamGeneratorPanel } from "./components/ExamGeneratorPanel";
import { HistoryDrawer } from "./components/HistoryDrawer";
import type { ExamPaperRecord } from "./api/client";

export type NavTab = "chat" | "notes" | "exam" | "generate" | "debug";

export default function App() {
  const [activeTab, setActiveTab] = useState<NavTab>("chat");
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [selectedConvId, setSelectedConvId] = useState<string | null>(null);
  const [selectedExam, setSelectedExam] = useState<ExamPaperRecord | null>(null);

  function handleSelectConversation(convId: string, mode: string) {
    setSelectedConvId(convId);
    if (mode === "notes_qa") {
      setActiveTab("notes");
    } else if (mode === "generate" || mode === "debug") {
      setActiveTab(mode);
    } else {
      setActiveTab("chat");
    }
    setIsHistoryOpen(false);
  }

  function handleSelectExam(paper: ExamPaperRecord) {
    setSelectedExam(paper);
    setActiveTab("exam");
    setIsHistoryOpen(false);
  }

  function handleNewSession() {
    setSelectedConvId(null);
    setSelectedExam(null);
    setIsHistoryOpen(false);
  }

  return (
    <div className="app">
      <StatusBar />

      {/* Main Feature Navigation Bar */}
      <nav className="main-nav-bar">
        <div className="main-tabs">
          <button
            type="button"
            className={`main-tab ${activeTab === "chat" ? "active" : ""}`}
            onClick={() => setActiveTab("chat")}
          >
            💬 Code Chat
          </button>
          <button
            type="button"
            className={`main-tab ${activeTab === "notes" ? "active" : ""}`}
            onClick={() => setActiveTab("notes")}
          >
            📚 Notes & Q&A (RAG)
          </button>
          <button
            type="button"
            className={`main-tab ${activeTab === "exam" ? "active" : ""}`}
            onClick={() => setActiveTab("exam")}
          >
            📝 Exam Generator
          </button>
          <button
            type="button"
            className={`main-tab ${activeTab === "generate" ? "active" : ""}`}
            onClick={() => setActiveTab("generate")}
          >
            ⚡ Generate Code
          </button>
          <button
            type="button"
            className={`main-tab ${activeTab === "debug" ? "active" : ""}`}
            onClick={() => setActiveTab("debug")}
          >
            🐞 Debug Assistant
          </button>
        </div>

        {/* Local Storage & History Toggle */}
        <div className="nav-actions">
          <button
            type="button"
            className="history-toggle-btn"
            onClick={() => setIsHistoryOpen(true)}
            title="Open locally saved chats & exams"
          >
            💾 Local History
          </button>
        </div>
      </nav>

      {/* Slide-out History Drawer */}
      <HistoryDrawer
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        onSelectConversation={handleSelectConversation}
        onSelectExam={handleSelectExam}
        onNewSession={handleNewSession}
      />

      {/* Active Feature Workspace */}
      <main className="main-content">
        {activeTab === "notes" && <NotesPanel initialConvId={selectedConvId} />}
        {activeTab === "exam" && <ExamGeneratorPanel initialExam={selectedExam} />}
        {(activeTab === "chat" || activeTab === "generate" || activeTab === "debug") && (
          <ChatPanel
            mode={activeTab}
            onModeChange={(m) => setActiveTab(m)}
            initialConvId={selectedConvId}
          />
        )}
      </main>
    </div>
  );
}
