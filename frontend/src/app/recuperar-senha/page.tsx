"use client";

import Link from "next/link";
import { useState } from "react";
import { formatUserError } from "@/lib/format-api-error";
import { createClient } from "@/lib/supabase/client";

export default function RecuperarSenhaPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setMessage("");
    setError("");

    const supabase = createClient();
    const redirectTo = `${window.location.origin}/auth/callback?next=/auth/reset-password`;

    const { error: resetError } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo,
    });

    if (resetError) {
      setError(formatUserError(resetError.message, "Não foi possível enviar o e-mail de recuperação."));
    } else {
      setMessage(
        "Se existir uma conta com este e-mail, você receberá um link para redefinir a senha.",
      );
    }

    setLoading(false);
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 px-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-lg">
        <div className="mb-8 text-center">
          <p className="text-xs font-semibold uppercase tracking-widest text-emerald-600">
            ACC Nomad
          </p>
          <h1 className="mt-2 text-2xl font-bold text-slate-900">Recuperar senha</h1>
          <p className="mt-1 text-sm text-slate-500">
            Enviaremos um link para redefinir sua senha
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">
              E-mail da conta
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
            />
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}
          {message && <p className="text-sm text-emerald-700">{message}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-emerald-600 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            {loading ? "Enviando…" : "Enviar link de recuperação"}
          </button>
        </form>

        <Link
          href="/login"
          className="mt-4 block w-full text-center text-sm text-emerald-600 hover:underline"
        >
          Voltar ao login
        </Link>
      </div>
    </div>
  );
}
