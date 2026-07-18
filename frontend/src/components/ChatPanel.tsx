"use client";
import { useState, useRef, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { chatApi } from "@/lib/api";
import { Send } from "lucide-react";
import { toast } from "sonner";

interface Message {
  role: "user" | "assistant";
  content: string;
  created_at?: string;
}

export function ChatPanel({ jobId }: { jobId: string }) {
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();

  const { data: history, isLoading } = useQuery({
    queryKey: ["chat-history", jobId],
    queryFn: () => chatApi.history(jobId).then((r) => r.data as Message[]),
  });

  const mutation = useMutation({
    mutationFn: (message: string) => chatApi.send(jobId, message),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chat-history", jobId] });
    },
    onError: () => toast.error("Failed to send message"),
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history, mutation.isPending]);

  const handleSend = () => {
    const msg = input.trim();
    if (!msg || mutation.isPending) return;
    setInput("");
    mutation.mutate(msg);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const SUGGESTIONS = [
    "What are the most important features?",
    "Which model performed best and why?",
    "What data quality issues were found?",
    "What business actions do you recommend?",
  ];

  return (
    <div className="bg-white rounded-xl border border-gray-200 flex flex-col h-[600px]">
      <div className="p-5 border-b border-gray-100">
        <h3 className="font-semibold text-gray-900">💬 Ask the AI Analyst</h3>
        <p className="text-xs text-gray-500 mt-0.5">Ask any question about your dataset or analysis results</p>
      </div>

      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {isLoading && <p className="text-gray-400 text-sm text-center">Loading history…</p>}

        {!history?.length && !isLoading && (
          <div className="text-center py-6">
            <p className="text-gray-400 text-sm mb-4">Start a conversation about your data</p>
            <div className="flex flex-wrap gap-2 justify-center">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => setInput(s)}
                  className="text-xs bg-gray-100 hover:bg-brand-50 hover:text-brand-700 text-gray-600 px-3 py-1.5 rounded-full transition"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {history?.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                msg.role === "user"
                  ? "bg-brand-600 text-white rounded-tr-sm"
                  : "bg-gray-100 text-gray-800 rounded-tl-sm"
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.content}</p>
            </div>
          </div>
        ))}

        {mutation.isPending && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-2xl rounded-tl-sm px-4 py-3">
              <div className="flex gap-1">
                {[0, 1, 2].map((i) => (
                  <div
                    key={i}
                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: `${i * 0.15}s` }}
                  />
                ))}
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="p-4 border-t border-gray-100">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about your dataset…"
            rows={1}
            className="flex-1 resize-none border border-gray-300 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || mutation.isPending}
            className="bg-brand-600 hover:bg-brand-500 text-white p-2.5 rounded-xl transition disabled:opacity-50"
            aria-label="Send message"
          >
            <Send size={18} />
          </button>
        </div>
        <p className="text-xs text-gray-400 mt-1.5 pl-1">Press Enter to send, Shift+Enter for new line</p>
      </div>
    </div>
  );
}
