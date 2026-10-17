export const API_BASE = "http://127.0.0.1:8765/api";

export interface HealthResponse {
  app: string;
  offline_mode: boolean;
  chat_model: string;
  embed_model: string;
  ollama: {
    reachable: boolean;
    models?: string[];
    chat_model_available?: boolean;
    error?: string;
  };
}

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

export type CodeLanguage = "python" | "javascript" | "typescript" | "react";

export interface CodegenRequest {
  prompt: string;
  language: CodeLanguage;
  include_explanation?: boolean;
  stream?: boolean;
}

export interface DebugRequest {
  code: string;
  error_message?: string;
  language: CodeLanguage;
  stream?: boolean;
}

export interface DocumentInfo {
  id: string;
  filename: string;
  file_type: string;
  size_bytes: number;
  chunk_count: number;
  char_count: number;
  created_at: string;
}

export interface SourceChunk {
  doc_id: string;
  filename: string;
  chunk_index: number;
  similarity: number;
  text: string;
}

export interface ExamGenerateRequest {
  title: string;
  subject: string;
  doc_ids?: string[];
  difficulty: "easy" | "medium" | "hard";
  total_marks: number;
  duration_minutes: number;
  include_solutions: boolean;
  model?: string;
  stream?: boolean;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error("Backend unreachable");
  return res.json();
}

export async function streamChat(
  messages: ChatMessage[],
  onToken: (token: string) => void,
  signal?: AbortSignal
): Promise<void> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, stream: true }),
    signal,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Chat request failed");
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error("No response stream");

  const decoder = new TextDecoder();
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    onToken(decoder.decode(value, { stream: true }));
  }
}

export async function streamCodegen(
  request: CodegenRequest,
  onToken: (token: string) => void,
  signal?: AbortSignal
): Promise<void> {
  const res = await fetch(`${API_BASE}/codegen/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...request, stream: true }),
    signal,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Codegen request failed");
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error("No response stream");

  const decoder = new TextDecoder();
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    onToken(decoder.decode(value, { stream: true }));
  }
}

export async function streamDebug(
  request: DebugRequest,
  onToken: (token: string) => void,
  signal?: AbortSignal
): Promise<void> {
  const res = await fetch(`${API_BASE}/debug/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...request, stream: true }),
    signal,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Debug request failed");
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error("No response stream");

  const decoder = new TextDecoder();
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    onToken(decoder.decode(value, { stream: true }));
  }
}

export async function fetchDocuments(): Promise<DocumentInfo[]> {
  const res = await fetch(`${API_BASE}/rag/documents`);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Failed to fetch documents");
  }
  return res.json();
}

export async function uploadDocument(file: File): Promise<DocumentInfo> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/rag/upload`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Failed to upload document");
  }
  return res.json();
}

export async function deleteDocument(docId: string): Promise<boolean> {
  const res = await fetch(`${API_BASE}/rag/documents/${docId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Failed to delete document");
  }
  return true;
}

export async function streamNotesQuery(
  question: string,
  docId: string | undefined,
  onToken: (token: string) => void,
  onSources?: (sources: SourceChunk[]) => void,
  signal?: AbortSignal
): Promise<void> {
  const res = await fetch(`${API_BASE}/rag/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      doc_id: docId || undefined,
      stream: true,
    }),
    signal,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Notes query failed");
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error("No response stream");

  const decoder = new TextDecoder();
  let buffer = "";
  let sourcesExtracted = false;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value, { stream: true });
    buffer += chunk;

    if (!sourcesExtracted) {
      const match = buffer.match(/^__SOURCES__:(.*?)\n\n([\s\S]*)$/);
      if (match) {
        try {
          const sources: SourceChunk[] = JSON.parse(match[1]);
          if (onSources) onSources(sources);
        } catch {
          // ignore parse error
        }
        sourcesExtracted = true;
        const remainder = match[2];
        if (remainder) {
          onToken(remainder);
        }
        buffer = "";
      } else if (!buffer.startsWith("__SOURCES__:")) {
        sourcesExtracted = true;
        onToken(buffer);
        buffer = "";
      }
    } else {
      onToken(chunk);
    }
  }
}

export async function streamExamGenerate(
  request: ExamGenerateRequest,
  onToken: (token: string) => void,
  signal?: AbortSignal
): Promise<void> {
  const res = await fetch(`${API_BASE}/rag/exam/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...request, stream: true }),
    signal,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Exam generation failed");
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error("No response stream");

  const decoder = new TextDecoder();
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    onToken(decoder.decode(value, { stream: true }));
  }
}

export function extractCodeBlock(text: string): string {
  const match = text.match(/```(?:\w+)?\n([\s\S]*?)```/);
  return match ? match[1].trim() : text.trim();
}

// --- History & Database Storage Types & APIs ---

export interface ConversationSummary {
  id: string;
  title: string;
  mode: string;
  created_at: string;
  updated_at: string;
}

export interface SavedMessage {
  id: string;
  conversation_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  sources?: SourceChunk[];
  timestamp: string;
}

export interface ConversationDetail {
  id: string;
  title: string;
  mode: string;
  created_at: string;
  updated_at: string;
  messages: SavedMessage[];
}

export interface ExamPaperRecord {
  id: string;
  title: string;
  subject: string;
  difficulty: string;
  total_marks: number;
  duration_minutes: number;
  content_markdown: string;
  created_at: string;
}

export async function fetchConversations(mode?: string): Promise<ConversationSummary[]> {
  const url = mode
    ? `${API_BASE}/history/conversations?mode=${encodeURIComponent(mode)}`
    : `${API_BASE}/history/conversations`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch conversations");
  return res.json();
}

export async function fetchConversation(id: string): Promise<ConversationDetail> {
  const res = await fetch(`${API_BASE}/history/conversations/${id}`);
  if (!res.ok) throw new Error("Failed to load conversation");
  return res.json();
}

export async function createConversation(
  title: string,
  mode: string,
  id?: string
): Promise<ConversationSummary> {
  const res = await fetch(`${API_BASE}/history/conversations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, mode, id }),
  });
  if (!res.ok) throw new Error("Failed to create conversation");
  return res.json();
}

export async function saveMessage(
  convId: string,
  role: string,
  content: string,
  sources?: any,
  id?: string
): Promise<SavedMessage> {
  const res = await fetch(`${API_BASE}/history/conversations/${convId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role, content, sources, id }),
  });
  if (!res.ok) throw new Error("Failed to save message");
  return res.json();
}

export async function deleteConversation(id: string): Promise<boolean> {
  const res = await fetch(`${API_BASE}/history/conversations/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete conversation");
  return true;
}

export async function fetchExamPapers(): Promise<ExamPaperRecord[]> {
  const res = await fetch(`${API_BASE}/history/exams`);
  if (!res.ok) throw new Error("Failed to fetch exam papers");
  return res.json();
}

export async function saveExamPaper(
  paper: Omit<ExamPaperRecord, "created_at">
): Promise<ExamPaperRecord> {
  const res = await fetch(`${API_BASE}/history/exams`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(paper),
  });
  if (!res.ok) throw new Error("Failed to save exam paper");
  return res.json();
}

export async function deleteExamPaper(id: string): Promise<boolean> {
  const res = await fetch(`${API_BASE}/history/exams/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete exam paper");
  return true;
}
