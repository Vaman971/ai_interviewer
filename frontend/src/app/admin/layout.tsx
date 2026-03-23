"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { Shield, Users, LayoutDashboard, Brain, LogOut } from "lucide-react";
import { useAuthStore } from "@/lib/stores";

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, hydrate, logout } = useAuthStore();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  useEffect(() => {
    if (!isAuthenticated) {
      if (typeof window !== "undefined" && !localStorage.getItem("access_token")) {
        router.push("/login");
      }
      return;
    }

    // Role Guard
    if (user && !user.is_admin) {
      router.push("/dashboard");
      return;
    }

    if (user && user.is_admin) {
      setLoading(false);
    }
  }, [isAuthenticated, user, router]);

  if (loading || !user) {
    return (
      <div style={{ height: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div className="spinner" />
      </div>
    );
  }

  const handleLogout = () => {
    logout();
    router.push("/");
  };

  const navLinks = [
    { href: "/admin", label: "Overview", icon: LayoutDashboard },
    { href: "/admin/users", label: "Users", icon: Users },
  ];

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      {/* ── Sidebar ────────────────────────────────────────────── */}
      <aside style={{ width: "250px", borderRight: "1px solid var(--border-color)", background: "rgba(10, 10, 15, 0.8)", padding: "24px", display: "flex", flexDirection: "column" }}>
        <Link href="/dashboard" style={{ display: "flex", alignItems: "center", gap: "10px", textDecoration: "none", marginBottom: "40px" }}>
          <div style={{ width: "32px", height: "32px", borderRadius: "8px", background: "var(--accent-gradient)", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Shield size={18} color="white" />
          </div>
          <span style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--text-primary)" }}>Admin Portal</span>
        </Link>
        
        <div style={{ display: "flex", flexDirection: "column", gap: "8px", flex: 1 }}>
          {navLinks.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link 
                key={link.href}
                href={link.href} 
                style={{ 
                  display: "flex", alignItems: "center", gap: "12px", padding: "12px 16px", borderRadius: "8px", textDecoration: "none",
                  background: isActive ? "rgba(124, 58, 237, 0.1)" : "transparent",
                  color: isActive ? "#a78bfa" : "var(--text-secondary)",
                  fontWeight: isActive ? 600 : 400
                }}
              >
                <link.icon size={18} />
                {link.label}
              </Link>
            );
          })}
        </div>

        <div style={{ marginTop: "auto", borderTop: "1px solid var(--border-color)", paddingTop: "24px" }}>
          <div style={{ marginBottom: "16px", color: "var(--text-muted)", fontSize: "0.85rem" }}>
            Logged in as:<br/>
            <span style={{ color: "var(--text-primary)", fontWeight: 500 }}>{user.email}</span>
            {user.is_super_admin && <span style={{ display: "block", color: "#f59e0b", fontSize: "0.75rem", marginTop: "4px" }}>Super Admin</span>}
          </div>
          <button onClick={handleLogout} className="btn-outline" style={{ width: "100%", padding: "8px", fontSize: "0.9rem" }}>
            <LogOut size={16} /> Logout
          </button>
        </div>
      </aside>

      {/* ── Main Content ───────────────────────────────────────── */}
      <main style={{ flex: 1, padding: "40px", overflowY: "auto" }}>
        {children}
      </main>
    </div>
  );
}
