"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MessageSquare, Send, Loader2, Bot, User, FileText, Plus } from "lucide-react";
import { useAuthStore } from "@/stores/auth-store";
import { conversationsApi, type Message, type Conversation } from "@/lib/api";
import ReactMarkdown from "react-markdown";

export default function ChatPage() {
  const token = useAuthStore((s) => s.token);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversation, setActiveConversation] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleNewConversation = async () => {
    if (!token) return;
    const conv = await conversationsApi.create("New Research Query", token);
    setConversations([conv, ...conversations]);
    setActiveConversation(conv.id);
    setMessages([]);
  };

  const handleSendMessage = async () => {
    if (!input.trim() || !token || !activeConversation) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      conversation_id: activeConversation,
      role: "user",
      content: input,
      agent_name: null,
      citations: null,
      execution_steps: null,
      latency_ms: null,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const response = await conversationsApi.sendMessage(activeConversation, input, token);
      setMessages((prev) => [...prev, response]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          conversation_id: activeConversation,
          role: "system",
          content: `Error: ${err.message || "Failed to process message"}`,
          agent_name: null,
          citations: null,
          execution_steps: null,
          latency_ms: null,
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto h-[calc(100vh-5rem)]">
      <div className="flex h-full gap-4">
        {/* Conversations sidebar */}
        <div className="w-72 glass-card flex flex-col">
          <div className="p-4 border-b border-surface-800">
            <button
              onClick={handleNewConversation}
              className="w-full py-2 rounded-lg bg-brand-600 hover:bg-brand-500 text-white text-sm font-medium flex items-center justify-center gap-2 transition-colors"
            >
              <Plus className="w-4 h-4" />
              New Chat
            </button>
          </div>
          <div className="flex-1 overflow-y-auto custom-scrollbar p-2 space-y-1">
            {conversations.length === 0 && (
              <p className="text-sm text-surface-500 text-center py-8">
                No conversations yet
              </p>
            )}
            {conversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => setActiveConversation(conv.id)}
                className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  activeConversation === conv.id
                    ? "bg-brand-500/10 text-brand-400 border border-brand-500/20"
                    : "text-surface-400 hover:bg-surface-800/50 hover:text-surface-200"
                }`}
              >
                <p className="truncate">{conv.title}</p>
                <p className="text-xs text-surface-500 mt-0.5">
                  {conv.message_count} messages
                </p>
              </button>
            ))}
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 glass-card flex flex-col">
          {!activeConversation ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <MessageSquare className="w-12 h-12 text-surface-600 mx-auto mb-4" />
                <h2 className="text-xl font-semibold text-surface-300 mb-2">
                  Start a conversation
                </h2>
                <p className="text-sm text-surface-500 mb-6">
                  Ask financial questions and get AI-powered, citation-backed answers
                </p>
                <button
                  onClick={handleNewConversation}
                  className="px-6 py-2.5 rounded-lg bg-brand-600 hover:bg-brand-500 text-white font-medium transition-colors"
                >
                  New Chat
                </button>
              </div>
            </div>
          ) : (
            <>
              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
                <AnimatePresence>
                  {messages.map((msg) => (
                    <motion.div
                      key={msg.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}
                    >
                      {msg.role !== "user" && (
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-accent-violet flex items-center justify-center flex-shrink-0">
                          <Bot className="w-4 h-4 text-white" />
                        </div>
                      )}
                      <div
                        className={`max-w-[70%] rounded-xl p-4 ${
                          msg.role === "user"
                            ? "bg-brand-600 text-white"
                            : "bg-surface-800 text-surface-200"
                        }`}
                      >
                        <div className="prose prose-sm prose-invert max-w-none">
                          <ReactMarkdown>{msg.content}</ReactMarkdown>
                        </div>

                        {/* Citations */}
                        {msg.citations && msg.citations.length > 0 && (
                          <div className="mt-3 pt-3 border-t border-surface-700/50 space-y-1">
                            <p className="text-xs text-surface-400 font-medium">Sources:</p>
                            {msg.citations.map((c, i) => (
                              <p key={i} className="text-xs text-brand-400">
                                [{i + 1}] {c.source}
                                {c.page ? `, Page ${c.page}` : ""}
                              </p>
                            ))}
                          </div>
                        )}

                        {/* Latency */}
                        {msg.latency_ms && (
                          <p className="text-[10px] text-surface-500 mt-2">
                            {(msg.latency_ms / 1000).toFixed(1)}s • {msg.agent_name || "orchestrator"}
                          </p>
                        )}
                      </div>
                      {msg.role === "user" && (
                        <div className="w-8 h-8 rounded-lg bg-surface-700 flex items-center justify-center flex-shrink-0">
                          <User className="w-4 h-4 text-surface-300" />
                        </div>
                      )}
                    </motion.div>
                  ))}
                </AnimatePresence>
                {loading && (
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-accent-violet flex items-center justify-center">
                      <Bot className="w-4 h-4 text-white" />
                    </div>
                    <div className="flex items-center gap-2 text-surface-400 text-sm">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Processing with multi-agent pipeline...
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <div className="p-4 border-t border-surface-800">
                <div className="relative">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSendMessage()}
                    placeholder="Ask a financial question..."
                    className="w-full pl-4 pr-14 py-3 rounded-xl bg-surface-800 border border-surface-700 text-surface-100 placeholder-surface-500 focus:border-brand-500 focus:ring-1 focus:ring-brand-500/50 transition-colors"
                  />
                  <button
                    onClick={handleSendMessage}
                    disabled={loading || !input.trim()}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-lg bg-brand-600 hover:bg-brand-500 text-white transition-colors disabled:opacity-50"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
