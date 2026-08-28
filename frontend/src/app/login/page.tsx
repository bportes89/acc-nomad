"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { formatUserError } from "@/lib/format-api-error";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [isSignUp, setIsSignUp] = useState(false);

  const infoMessage =
    searchParams.get("msg") === "password_updated"
      ? "Senha atualizada com sucesso! Faça login com a nova senha."
      : searchParams.get("error") === "missing_env"
        ? "Configure NEXT_PUBLIC_SUPABASE_URL e NEXT_PUBLIC_SUPABASE_ANON_KEY no .env.local"
        : "";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");

    const supabase = createClient();
    const redirectTo = `${window.location.origin}/auth/callback?next=/dashboard`;

    if (isSignUp) {
      const { error: signUpError } = await supabase.auth.signUp({
        email,
        password,
        options: { emailRedirectTo: redirectTo },
      });
      if (signUpError) {
        setError(formatUserError(signUpError.message, "Não foi possível criar a conta."));
        setLoading(false);
        return;
      }
      setError("Conta criada! Verifique seu e-mail ou faça login.");
      setLoading(false);
      return;
    }

    const { error: signInError } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (signInError) {
      setError(formatUserError(signInError.message, "Não foi possível entrar."));
      setLoading(false);
      return;
    }

    router.push("/dashboard");
    router.refresh();
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 px-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-lg">
        <div className="mb-8 text-center">
          <p className="text-xs font-semibold uppercase tracking-widest text-emerald-600">
            ACC Nomad
          </p>
          <h1 className="mt-2 text-2xl font-bold text-slate-900">
            {isSignUp ? "Criar conta" : "Entrar"}
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Automação de Controle Contábil
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">
              E-mail
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
            />
          </div>
          <div>
            <div className="mb-1 flex items-center justify-between">
              <label className="block text-sm font-medium text-slate-700">
                Senha
              </label>
              {!isSignUp && (
                <Link
                  href="/recuperar-senha"
                  className="text-xs text-emerald-600 hover:underline"
                >
                  Esqueci minha senha
                </Link>
              )}
            </div>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
              className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
            />
          </div>

          {infoMessage && (
            <p className="text-sm text-emerald-700">{infoMessage}</p>
          )}
          {error && (
            <p className={`text-sm ${error.includes("Conta criada") ? "text-emerald-700" : "text-red-600"}`}>
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-emerald-600 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            {loading ? "Aguarde…" : isSignUp ? "Criar conta" : "Entrar"}
          </button>
        </form>

        <button
          type="button"
          onClick={() => setIsSignUp(!isSignUp)}
          className="mt-4 w-full text-center text-sm text-emerald-600 hover:underline"
        >
          {isSignUp ? "Já tenho conta" : "Criar nova conta"}
        </button>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-slate-100">
          <p className="text-sm text-slate-500">Carregando…</p>
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
