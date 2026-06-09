"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles,
  LayoutDashboard,
  Search,
  FileText,
  Upload,
  MessageSquare,
  Database,
  BarChart3,
  Settings,
  Shield,
  LogOut,
  Menu,
  X,
  ChevronRight,
  Star,
} from "lucide-react";
import { useAuthStore } from "@/stores/auth-store";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/dashboard/research", label: "Research", icon: Search },
  { href: "/dashboard/portfolio", label: "Portfolio Mode", icon: Star, highlight: true },
  { href: "/dashboard/chat", label: "Chat", icon: MessageSquare },
  { href: "/dashboard/documents", label: "Documents", icon: Upload },
  { href: "/dashboard/reports", label: "Reports", icon: FileText },
  { href: "/dashboard/knowledge", label: "Knowledge Base", icon: Database },
];

const bottomNavItems = [
  { href: "/dashboard/settings", label: "Settings", icon: Settings },
  { href: "/dashboard/admin", label: "Admin Panel", icon: Shield, adminOnly: true },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuthStore();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  const isActive = (href: string) => {
    if (href === "/dashboard") return pathname === "/dashboard";
    return pathname.startsWith(href);
  };

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside
        className={`${
          sidebarOpen ? "w-64" : "w-16"
        } fixed left-0 top-0 h-screen border-r border-surface-800 bg-surface-950/95 backdrop-blur-xl flex flex-col transition-all duration-300 z-40`}
      >
        {/* Logo */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-surface-800">
          <Link href="/dashboard" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-accent-violet flex items-center justify-center flex-shrink-0">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            {sidebarOpen && (
              <motion.span
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-lg font-bold"
              >
                FinSight AI
              </motion.span>
            )}
          </Link>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-1 rounded-md hover:bg-surface-800 text-surface-400 hover:text-surface-200 transition-colors"
          >
            {sidebarOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto custom-scrollbar">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 group ${
                isActive(item.href)
                  ? "bg-brand-500/10 text-brand-400 border border-brand-500/20"
                  : "text-surface-400 hover:text-surface-200 hover:bg-surface-800/50"
              } ${item.highlight && !isActive(item.href) ? "text-accent-amber hover:text-accent-amber" : ""}`}
            >
              <item.icon className={`w-5 h-5 flex-shrink-0 ${
                item.highlight && !isActive(item.href) ? "text-accent-amber" : ""
              }`} />
              {sidebarOpen && (
                <span className="flex-1">{item.label}</span>
              )}
              {sidebarOpen && item.highlight && (
                <span className="px-1.5 py-0.5 text-[10px] font-bold rounded-full bg-accent-amber/20 text-accent-amber">
                  NEW
                </span>
              )}
            </Link>
          ))}
        </nav>

        {/* Bottom section */}
        <div className="px-3 py-4 border-t border-surface-800 space-y-1">
          {bottomNavItems.map((item) => {
            if (item.adminOnly && user?.role !== "admin") return null;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                  isActive(item.href)
                    ? "bg-brand-500/10 text-brand-400"
                    : "text-surface-400 hover:text-surface-200 hover:bg-surface-800/50"
                }`}
              >
                <item.icon className="w-5 h-5 flex-shrink-0" />
                {sidebarOpen && <span>{item.label}</span>}
              </Link>
            );
          })}

          {/* User profile */}
          <div className="flex items-center gap-3 px-3 py-2 mt-2">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-brand-500 to-accent-violet flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
              {user?.name?.charAt(0) || "U"}
            </div>
            {sidebarOpen && (
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-surface-200 truncate">
                  {user?.name || "User"}
                </p>
                <p className="text-xs text-surface-500 truncate">{user?.email}</p>
              </div>
            )}
            {sidebarOpen && (
              <button
                onClick={handleLogout}
                className="p-1 rounded-md hover:bg-surface-800 text-surface-500 hover:text-accent-rose transition-colors"
                title="Sign out"
              >
                <LogOut className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main
        className={`flex-1 ${sidebarOpen ? "ml-64" : "ml-16"} transition-all duration-300`}
      >
        <div className="min-h-screen p-6">{children}</div>
      </main>
    </div>
  );
}
