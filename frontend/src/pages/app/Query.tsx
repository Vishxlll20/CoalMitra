import { useEffect, useState, useRef } from "react";
import { MessageSquareText, Send, Languages, Mic, MicOff } from "lucide-react";
import { api } from "../../lib/api";
import { PageHeader } from "../../components/shared/PageHeader";
import { EmptyState } from "../../components/shared/EmptyState";
import { CardSkeleton } from "../../components/shared/LoadingSkeleton";
import { SourcePill } from "../../components/shared/SourcePill";
import { Button } from "../../components/ui/Button";
import type { ChatMessage } from "../../types";
import { toast } from "sonner";

export function Query() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [language, setLanguage] = useState<"en" | "hi">("en");
  const [loading, setLoading] = useState(false);
  const [sessionLoading, setSessionLoading] = useState(true);
  const [recording, setRecording] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const mediaRef = useRef<MediaRecorder | null>(null);

  // Create session on mount
  useEffect(() => {
    api.chat
      .create("CoalMitra demo session")
      .then((s) => {
        setSessionId(s.id);
        return api.chat.messages(s.id);
      })
      .then(setMessages)
      .catch(() => {})
      .finally(() => setSessionLoading(false));
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!sessionId || !input.trim() || loading) return;
    const text = input.trim();
    setInput("");
    setLoading(true);
    try {
      const reply = await api.chat.query(sessionId, text, language);
      setMessages((prev) => [...prev, { id: "u-" + Date.now(), role: "user", content: text, language, mode: "text", confidence: 0, response_ms: 0, citations: [] }, reply]);
    } catch {
      toast.error("Query failed — try again");
    } finally {
      setLoading(false);
    }
  };

  const toggleRecording = async () => {
    if (recording) {
      mediaRef.current?.stop();
      setRecording(false);
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      const chunks: Blob[] = [];
      recorder.ondataavailable = (e) => chunks.push(e.data);
      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunks, { type: "audio/webm" });
        if (blob.size < 100) return;
        setLoading(true);
        try {
          const reply = await api.chat.voice(sessionId!, blob, language);
          setMessages((prev) => [...prev, { id: "v-" + Date.now(), role: "user", content: "🎤 Voice query", language, mode: "voice", confidence: 0, response_ms: 0, citations: [] }, reply]);
        } catch {
          toast.error("Voice transcription failed");
        } finally {
          setLoading(false);
        }
      };
      recorder.start();
      mediaRef.current = recorder;
      setRecording(true);
    } catch {
      toast.error("Microphone access denied");
    }
  };

  return (
    <div className="flex h-[calc(100vh-120px)] flex-col space-y-0">
      <div className="mb-4">
        <PageHeader
          title="AI Query"
          description="Ask in English or हिंदी — answers are grounded in document evidence."
          eyebrow="AI Query"
          actions={
            <div className="flex items-center gap-2">
              <button
                onClick={() => setLanguage((l) => (l === "en" ? "hi" : "en"))}
                className="inline-flex items-center gap-1.5 rounded-md border hairline bg-white px-3 py-1.5 text-[12px] font-medium text-ink/60 transition-colors hover:text-ink"
              >
                <Languages className="h-3.5 w-3.5" />
                {language === "en" ? "English" : "हिंदी"}
              </button>
            </div>
          }
        />
      </div>

      {/* Messages area */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto rounded-xl border border-slate-200 bg-white">
        {sessionLoading ? (
          <div className="p-6"><CardSkeleton rows={3} /></div>
        ) : messages.length === 0 ? (
          <div className="flex h-full items-center justify-center p-12">
            <EmptyState
              icon={<MessageSquareText className="h-6 w-6" />}
              title="Ask CoalMitra anything"
              copy={language === "hi"
                ? "हिंदी या अंग्रेज़ी में प्रश्न पूछें। उत्तर दस्तावेज़ साक्ष्य पर आधारित होते हैं।"
                : "Questions about coal reserves, quality parameters, block data — grounded in document evidence with citations."}
            />
          </div>
        ) : (
          <div className="space-y-0 p-4">
            {messages.map((m, i) => (
              <MessageBubble key={m.id ?? i} msg={m} />
            ))}
            {loading && (
              <div className="flex gap-3 px-4 py-3">
                <div className="h-8 w-8 rounded-full bg-gold-500/15 flex items-center justify-center">
                  <span className="text-gold-600 text-[11px] font-bold">AI</span>
                </div>
                <div className="flex items-center gap-1.5 rounded-lg bg-slate-100 px-3.5 py-2.5">
                  <span className="inline-block h-1.5 w-1.5 animate-pulse-bar rounded-full bg-navy-600" />
                  <span className="inline-block h-2 w-1.5 animate-pulse-bar rounded-full bg-navy-600" style={{ animationDelay: "0.15s" }} />
                  <span className="inline-block h-1.5 w-1.5 animate-pulse-bar rounded-full bg-navy-600" style={{ animationDelay: "0.3s" }} />
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Input area */}
      <div className="mt-3 flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
          placeholder={language === "hi" ? "हिंदी या अंग्रेज़ी में प्रश्न लिखें…" : "Ask about coalfields, reserves, quality…"}
          className="flex-1 bg-transparent text-[14px] text-ink outline-none placeholder:text-ink/35"
          disabled={loading}
        />
        <button
          onClick={toggleRecording}
          className={`flex h-9 w-9 items-center justify-center rounded-lg transition-colors ${
            recording ? "bg-danger/10 text-danger animate-pulse" : "bg-slate-100 text-ink/50 hover:text-ink"
          }`}
          title={recording ? "Stop recording" : "Record voice query"}
        >
          {recording ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
        </button>
        <Button
          variant="gold"
          size="sm"
          onClick={handleSend}
          disabled={loading || !input.trim()}
        >
          <Send className="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>
  );
}

function MessageBubble({ msg }: { msg: ChatMessage }) {
  const isUser = msg.role === "user";
  return (
    <div className={`flex gap-3 px-4 py-3 ${isUser ? "justify-end" : ""}`}>
      {!isUser && (
        <div className="h-8 w-8 shrink-0 rounded-full bg-gold-500/15 flex items-center justify-center">
          <span className="text-gold-600 text-[11px] font-bold">AI</span>
        </div>
      )}
      <div className={`max-w-[75%] ${isUser ? "order-first" : ""}`}>
        <div
          className={`rounded-xl px-4 py-3 text-[14px] leading-relaxed ${
            isUser
              ? "bg-navy-900 text-paper ml-auto"
              : "bg-slate-100 text-ink"
          }`}
        >
          {msg.content}
          {isUser && msg.mode === "voice" && (
            <span className="ml-2 inline-flex items-center gap-1 text-[11px] opacity-60">
              <Mic className="h-3 w-3" /> voice
            </span>
          )}
        </div>

        {/* Citations (assistant only) */}
        {!isUser && msg.citations?.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {msg.citations.map((c, i) => (
              <SourcePill
                key={c.id ?? i}
                refData={{
                  document_id: c.document_id,
                  document_title: c.document_title,
                  display: c.document_title ?? `p.${c.page_number}`,
                  page: c.page_number,
                  bbox: c.bbox,
                  confidence: c.score,
                  value: c.rank,
                }}
                origin="chat"
                label={`Ref ${c.rank + 1}`}
              />
            ))}
          </div>
        )}

        {/* Confidence + timing */}
        {!isUser && msg.confidence > 0 && (
          <div className="mt-1.5 flex items-center gap-2.5 text-[10.5px] text-ink/35">
            <ConfidenceDot confidence={msg.confidence} />
            <span>{Math.round(msg.confidence * 100)}% confidence</span>
            <span>·</span>
            <span>{msg.response_ms}ms</span>
          </div>
        )}
      </div>
    </div>
  );
}

function ConfidenceDot({ confidence }: { confidence: number }) {
  const color = confidence >= 0.85 ? "bg-success" : confidence >= 0.65 ? "bg-info" : "bg-danger";
  return <span className={`h-1.5 w-1.5 rounded-full ${color}`} />;
}