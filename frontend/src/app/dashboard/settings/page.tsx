"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Settings as SettingsIcon,
  User,
  Key,
  Cpu,
  Bell,
  Palette,
  Save,
  Eye,
  EyeOff,
  CheckCircle2,
  Moon,
  Sun,
  Monitor,
} from "lucide-react";
import { useAuthStore } from "@/stores/auth-store";

type TabId = "profile" | "apikeys" | "ai" | "notifications" | "appearance";

const tabs: { id: TabId; label: string; icon: typeof User }[] = [
  { id: "profile", label: "Profile", icon: User },
  { id: "apikeys", label: "API Keys", icon: Key },
  { id: "ai", label: "AI Provider", icon: Cpu },
  { id: "notifications", label: "Notifications", icon: Bell },
  { id: "appearance", label: "Appearance", icon: Palette },
];

export default function SettingsPage() {
  const { user } = useAuthStore();
  const [activeTab, setActiveTab] = useState<TabId>("profile");
  const [saved, setSaved] = useState(false);

  // Profile state
  const [name, setName] = useState(user?.name || "");
  const [email] = useState(user?.email || "");

  // API Keys state
  const [geminiKey, setGeminiKey] = useState("");
  const [openaiKey, setOpenaiKey] = useState("");
  const [showGemini, setShowGemini] = useState(false);
  const [showOpenai, setShowOpenai] = useState(false);

  // AI Provider state
  const [llmProvider, setLlmProvider] = useState<"gemini" | "openai">("gemini");
  const [embeddingProvider, setEmbeddingProvider] = useState<"gemini" | "openai">("gemini");
  const [geminiModel, setGeminiModel] = useState("gemini-2.0-flash");
  const [openaiModel, setOpenaiModel] = useState("gpt-4o-mini");

  // Notification state
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [reportReady, setReportReady] = useState(true);
  const [weeklyDigest, setWeeklyDigest] = useState(false);
  const [agentErrors, setAgentErrors] = useState(true);

  // Appearance state
  const [theme, setTheme] = useState<"dark" | "light" | "system">("dark");

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2.5 rounded-xl bg-gradient-to-br from-surface-600 to-surface-700">
          <SettingsIcon className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-bold">Settings</h1>
          <p className="text-surface-400">
            Manage your profile, API keys, and preferences
          </p>
        </div>
      </div>

      <div className="flex gap-6">
        {/* Tab Navigation */}
        <div className="w-52 flex-shrink-0">
          <nav className="space-y-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? "bg-brand-500/10 text-brand-400 border border-brand-500/20"
                    : "text-surface-400 hover:text-surface-200 hover:bg-surface-800/50"
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="flex-1">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card p-6"
          >
            {/* Profile Tab */}
            {activeTab === "profile" && (
              <div className="space-y-6">
                <h2 className="text-lg font-semibold">Profile Settings</h2>

                <div className="flex items-center gap-4 mb-6">
                  <div className="w-16 h-16 rounded-full bg-gradient-to-br from-brand-500 to-accent-violet flex items-center justify-center text-white text-2xl font-bold">
                    {name.charAt(0) || "U"}
                  </div>
                  <div>
                    <p className="font-medium text-surface-200">{name || "User"}</p>
                    <p className="text-sm text-surface-500">{email}</p>
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm text-surface-400 mb-1.5">Display Name</label>
                    <input
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="w-full px-4 py-2.5 rounded-lg bg-surface-800 border border-surface-700 text-surface-100 focus:border-brand-500 focus:ring-1 focus:ring-brand-500/50 transition-colors"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-surface-400 mb-1.5">Email Address</label>
                    <input
                      type="email"
                      value={email}
                      disabled
                      className="w-full px-4 py-2.5 rounded-lg bg-surface-800/50 border border-surface-700 text-surface-500 cursor-not-allowed"
                    />
                    <p className="text-xs text-surface-600 mt-1">Email cannot be changed after registration</p>
                  </div>
                </div>
              </div>
            )}

            {/* API Keys Tab */}
            {activeTab === "apikeys" && (
              <div className="space-y-6">
                <h2 className="text-lg font-semibold">API Key Management</h2>
                <p className="text-sm text-surface-400">
                  Configure your AI provider API keys. Keys are encrypted and stored securely.
                </p>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm text-surface-400 mb-1.5">
                      Google Gemini API Key
                    </label>
                    <div className="relative">
                      <input
                        type={showGemini ? "text" : "password"}
                        value={geminiKey}
                        onChange={(e) => setGeminiKey(e.target.value)}
                        placeholder="AIza..."
                        className="w-full px-4 py-2.5 pr-10 rounded-lg bg-surface-800 border border-surface-700 text-surface-100 placeholder-surface-600 focus:border-brand-500 focus:ring-1 focus:ring-brand-500/50 transition-colors font-mono text-sm"
                      />
                      <button
                        onClick={() => setShowGemini(!showGemini)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-surface-500 hover:text-surface-300 transition-colors"
                      >
                        {showGemini ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm text-surface-400 mb-1.5">
                      OpenAI API Key
                    </label>
                    <div className="relative">
                      <input
                        type={showOpenai ? "text" : "password"}
                        value={openaiKey}
                        onChange={(e) => setOpenaiKey(e.target.value)}
                        placeholder="sk-..."
                        className="w-full px-4 py-2.5 pr-10 rounded-lg bg-surface-800 border border-surface-700 text-surface-100 placeholder-surface-600 focus:border-brand-500 focus:ring-1 focus:ring-brand-500/50 transition-colors font-mono text-sm"
                      />
                      <button
                        onClick={() => setShowOpenai(!showOpenai)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-surface-500 hover:text-surface-300 transition-colors"
                      >
                        {showOpenai ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-accent-amber/5 border border-accent-amber/20">
                  <p className="text-xs text-accent-amber">
                    🔒 Keys are encrypted using AES-256 before storage. They are never logged or exposed in API responses.
                  </p>
                </div>
              </div>
            )}

            {/* AI Provider Tab */}
            {activeTab === "ai" && (
              <div className="space-y-6">
                <h2 className="text-lg font-semibold">AI Provider Configuration</h2>

                <div className="space-y-5">
                  <div>
                    <label className="block text-sm text-surface-400 mb-2">Primary LLM Provider</label>
                    <div className="flex gap-3">
                      {(["gemini", "openai"] as const).map((provider) => (
                        <button
                          key={provider}
                          onClick={() => setLlmProvider(provider)}
                          className={`flex-1 p-4 rounded-lg border transition-all ${
                            llmProvider === provider
                              ? "border-brand-500/40 bg-brand-500/5 ring-1 ring-brand-500/20"
                              : "border-surface-700 hover:border-surface-500"
                          }`}
                        >
                          <p className="font-semibold text-surface-200 capitalize">{provider}</p>
                          <p className="text-xs text-surface-500 mt-1">
                            {provider === "gemini" ? "Gemini 2.0 Flash" : "GPT-4o Mini"}
                          </p>
                          {llmProvider === provider && (
                            <CheckCircle2 className="w-4 h-4 text-brand-400 mt-2" />
                          )}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm text-surface-400 mb-2">Embedding Provider</label>
                    <div className="flex gap-3">
                      {(["gemini", "openai"] as const).map((provider) => (
                        <button
                          key={provider}
                          onClick={() => setEmbeddingProvider(provider)}
                          className={`flex-1 p-4 rounded-lg border transition-all ${
                            embeddingProvider === provider
                              ? "border-brand-500/40 bg-brand-500/5 ring-1 ring-brand-500/20"
                              : "border-surface-700 hover:border-surface-500"
                          }`}
                        >
                          <p className="font-semibold text-surface-200 capitalize">{provider}</p>
                          <p className="text-xs text-surface-500 mt-1">
                            {provider === "gemini" ? "text-embedding-004" : "text-embedding-3-small"}
                          </p>
                          {embeddingProvider === provider && (
                            <CheckCircle2 className="w-4 h-4 text-brand-400 mt-2" />
                          )}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm text-surface-400 mb-1.5">Gemini Model</label>
                      <select
                        value={geminiModel}
                        onChange={(e) => setGeminiModel(e.target.value)}
                        className="w-full px-4 py-2.5 rounded-lg bg-surface-800 border border-surface-700 text-surface-200 focus:border-brand-500 transition-colors"
                      >
                        <option value="gemini-2.0-flash">Gemini 2.0 Flash</option>
                        <option value="gemini-2.0-flash-lite">Gemini 2.0 Flash Lite</option>
                        <option value="gemini-2.5-pro">Gemini 2.5 Pro</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm text-surface-400 mb-1.5">OpenAI Model</label>
                      <select
                        value={openaiModel}
                        onChange={(e) => setOpenaiModel(e.target.value)}
                        className="w-full px-4 py-2.5 rounded-lg bg-surface-800 border border-surface-700 text-surface-200 focus:border-brand-500 transition-colors"
                      >
                        <option value="gpt-4o-mini">GPT-4o Mini</option>
                        <option value="gpt-4o">GPT-4o</option>
                        <option value="gpt-4-turbo">GPT-4 Turbo</option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Notifications Tab */}
            {activeTab === "notifications" && (
              <div className="space-y-6">
                <h2 className="text-lg font-semibold">Notification Preferences</h2>

                <div className="space-y-4">
                  {[
                    { label: "Email Notifications", desc: "Receive notifications via email", state: emailNotifications, setter: setEmailNotifications },
                    { label: "Report Ready", desc: "Notify when a report finishes generating", state: reportReady, setter: setReportReady },
                    { label: "Weekly Digest", desc: "Weekly summary of platform activity", state: weeklyDigest, setter: setWeeklyDigest },
                    { label: "Agent Errors", desc: "Alert when agent pipeline encounters errors", state: agentErrors, setter: setAgentErrors },
                  ].map((item) => (
                    <div key={item.label} className="flex items-center justify-between p-4 rounded-lg bg-surface-800/30 border border-surface-700/50">
                      <div>
                        <p className="text-sm font-medium text-surface-200">{item.label}</p>
                        <p className="text-xs text-surface-500 mt-0.5">{item.desc}</p>
                      </div>
                      <button
                        onClick={() => item.setter(!item.state)}
                        className={`relative w-11 h-6 rounded-full transition-colors ${
                          item.state ? "bg-brand-500" : "bg-surface-700"
                        }`}
                      >
                        <span
                          className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform ${
                            item.state ? "translate-x-5" : "translate-x-0"
                          }`}
                        />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Appearance Tab */}
            {activeTab === "appearance" && (
              <div className="space-y-6">
                <h2 className="text-lg font-semibold">Appearance</h2>

                <div>
                  <label className="block text-sm text-surface-400 mb-3">Theme</label>
                  <div className="grid grid-cols-3 gap-3">
                    {([
                      { id: "dark" as const, label: "Dark", icon: Moon },
                      { id: "light" as const, label: "Light", icon: Sun },
                      { id: "system" as const, label: "System", icon: Monitor },
                    ]).map((t) => (
                      <button
                        key={t.id}
                        onClick={() => setTheme(t.id)}
                        className={`p-4 rounded-lg border text-center transition-all ${
                          theme === t.id
                            ? "border-brand-500/40 bg-brand-500/5 ring-1 ring-brand-500/20"
                            : "border-surface-700 hover:border-surface-500"
                        }`}
                      >
                        <t.icon className={`w-5 h-5 mx-auto mb-2 ${
                          theme === t.id ? "text-brand-400" : "text-surface-400"
                        }`} />
                        <p className="text-sm font-medium text-surface-200">{t.label}</p>
                      </button>
                    ))}
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-surface-800/50 border border-surface-700/50">
                  <p className="text-xs text-surface-500">
                    🎨 The platform is optimized for dark mode. Light mode support is coming soon.
                  </p>
                </div>
              </div>
            )}

            {/* Save Button */}
            <div className="flex justify-end mt-6 pt-4 border-t border-surface-800">
              <button
                onClick={handleSave}
                className={`px-6 py-2.5 rounded-lg font-medium text-sm flex items-center gap-2 transition-all ${
                  saved
                    ? "bg-accent-emerald/20 text-accent-emerald border border-accent-emerald/30"
                    : "bg-brand-500 hover:bg-brand-600 text-white"
                }`}
              >
                {saved ? (
                  <>
                    <CheckCircle2 className="w-4 h-4" />
                    Saved
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4" />
                    Save Changes
                  </>
                )}
              </button>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
