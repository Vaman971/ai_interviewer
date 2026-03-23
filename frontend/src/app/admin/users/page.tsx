"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import toast from "react-hot-toast";
import { adminApi } from "@/lib/api";
import { useAuthStore } from "@/lib/stores";

interface AdminUser {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_admin: boolean;
  is_super_admin: boolean;
  created_at: string;
}

export default function AdminUsersPage() {
  const { user } = useAuthStore();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      const data = await adminApi.getUsers();
      setUsers(data.users);
    } catch {
      toast.error("Failed to load users");
    } finally {
      setLoading(false);
    }
  };

  const handleToggleAdmin = async (targetUser: AdminUser) => {
    if (!user?.is_super_admin) {
      toast.error("Only the Super Admin can modify roles.");
      return;
    }
    const makeAdmin = !targetUser.is_admin;
    
    // Optimistic UI checks
    if (makeAdmin && !targetUser.email.endsWith("@aiinterviewer.com")) {
      toast.error("Admins must have an @aiinterviewer.com email address.");
      return;
    }

    try {
      if (confirm(`Are you sure you want to ${makeAdmin ? 'grant' : 'revoke'} admin rights for ${targetUser.email}?`)) {
        await adminApi.modifyRole(targetUser.id, makeAdmin);
        toast.success(`Roles updated for ${targetUser.email}`);
        
        // Update local state
        setUsers(users.map(u => u.id === targetUser.id ? { ...u, is_admin: makeAdmin } : u));
      }
    } catch (err: any) {
      toast.error(err.message || "Failed to update role");
    }
  };

  if (loading) return <div className="spinner" style={{ margin: "40px auto" }} />;

  return (
    <div>
      <h1 style={{ fontSize: "2rem", fontWeight: 700, marginBottom: "32px", color: "var(--text-primary)" }}>User Management</h1>
      
      <div className="glass-card" style={{ overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
          <thead>
            <tr style={{ background: "rgba(255, 255, 255, 0.05)", borderBottom: "1px solid var(--border-color)" }}>
              <th style={{ padding: "16px 24px", fontWeight: 600, color: "var(--text-secondary)", fontSize: "0.85rem", textTransform: "uppercase" }}>Email</th>
              <th style={{ padding: "16px 24px", fontWeight: 600, color: "var(--text-secondary)", fontSize: "0.85rem", textTransform: "uppercase" }}>Name</th>
              <th style={{ padding: "16px 24px", fontWeight: 600, color: "var(--text-secondary)", fontSize: "0.85rem", textTransform: "uppercase" }}>Joined</th>
              <th style={{ padding: "16px 24px", fontWeight: 600, color: "var(--text-secondary)", fontSize: "0.85rem", textTransform: "uppercase" }}>Role</th>
              <th style={{ padding: "16px 24px", fontWeight: 600, color: "var(--text-secondary)", fontSize: "0.85rem", textTransform: "uppercase", textAlign: "right" }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u, i) => (
              <motion.tr 
                key={u.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: i * 0.05 }}
                style={{ borderBottom: "1px solid var(--border-color)" }}
              >
                <td style={{ padding: "16px 24px", color: "var(--text-primary)" }}>{u.email}</td>
                <td style={{ padding: "16px 24px", color: "var(--text-muted)" }}>{u.full_name || "—"}</td>
                <td style={{ padding: "16px 24px", color: "var(--text-muted)" }}>
                  {new Date(u.created_at).toLocaleDateString()}
                </td>
                <td style={{ padding: "16px 24px" }}>
                  {u.is_super_admin ? (
                    <span className="badge badge-warning" style={{ background: "#f59e0b20", color: "#f59e0b" }}>Super Admin</span>
                  ) : u.is_admin ? (
                    <span className="badge badge-purple" style={{ background: "#8b5cf620", color: "#8b5cf6" }}>Admin</span>
                  ) : (
                    <span className="badge badge-info" style={{ background: "#3b82f620", color: "#3b82f6" }}>User</span>
                  )}
                </td>
                <td style={{ padding: "16px 24px", textAlign: "right" }}>
                  {user?.is_super_admin && !u.is_super_admin && (
                    <button 
                      onClick={() => handleToggleAdmin(u)}
                      className={u.is_admin ? "btn-outline" : "btn-gradient"} 
                      style={{ padding: "6px 12px", fontSize: "0.8rem", width: "110px" }}
                    >
                      {u.is_admin ? "Revoke Admin" : "Make Admin"}
                    </button>
                  )}
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
