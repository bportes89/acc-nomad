"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  BarChart3,
  Building2,
  ClipboardCheck,
  FileUp,
  HelpCircle,
  LayoutDashboard,
  LogOut,
  Truck,
  Wallet,
} from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import { cn } from "@/lib/utils";

const links = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/empresas", label: "Empresas", icon: Building2 },
  { href: "/upload", label: "Upload", icon: FileUp },
  { href: "/revisao", label: "Revisão", icon: ClipboardCheck },
  { href: "/fornecedores", label: "Fornecedores", icon: Truck },
  { href: "/tesouraria", label: "Tesouraria", icon: Wallet },
  { href: "/pmg", label: "PMG", icon: BarChart3 },
  { href: "/suporte", label: "Suporte", icon: HelpCircle },
];

export function Sidebar({ email }: { email: string }) {
  const pathname = usePathname();
  const router = useRouter();

  async function handleLogout() {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/login");
    router.refresh();
  }

  return (
    <aside className="flex h-screen w-64 flex-col bg-slate-900 text-white">
      <div className="border-b border-slate-700 px-6 py-5">
        <p className="text-xs font-semibold uppercase tracking-widest text-emerald-400">
          ACC Nomad
        </p>
        <p className="mt-1 text-sm text-slate-400">Controle Contábil</p>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4">
        {links.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
              pathname === href
                ? "bg-emerald-600 text-white"
                : "text-slate-300 hover:bg-slate-800 hover:text-white",
            )}
          >
            <Icon size={18} />
            {label}
          </Link>
        ))}
      </nav>

      <div className="border-t border-slate-700 px-4 py-4">
        <p className="truncate text-xs text-slate-400">{email}</p>
        <button
          onClick={handleLogout}
          className="mt-3 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-300 hover:bg-slate-800 hover:text-white"
        >
          <LogOut size={16} />
          Sair
        </button>
      </div>
    </aside>
  );
}
