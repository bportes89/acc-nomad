"use client";

import { useRouter } from "next/navigation";
import { Trash2 } from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import type { Extrato } from "@/lib/types";

export function ExtratoActions({ extrato }: { extrato: Extrato }) {
  const router = useRouter();

  async function excluir() {
    if (!confirm(`Excluir extrato "${extrato.nome_arquivo}"?`)) return;

    const supabase = createClient();
    await supabase.from("extratos").delete().eq("id", extrato.id);
    router.refresh();
  }

  if (extrato.status !== "pendente" && extrato.status !== "erro") return null;

  return (
    <button
      onClick={excluir}
      title="Excluir e reenviar"
      className="rounded p-1 text-red-500 hover:bg-red-50"
    >
      <Trash2 size={16} />
    </button>
  );
}
