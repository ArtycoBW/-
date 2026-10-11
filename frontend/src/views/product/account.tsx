"use client";
import { useToast } from "@/components/product/toasts";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PageHead } from "@/components/product/page";
import { Field, Notice } from "@/components/product/ui";
import { api, post, User, date } from "@/lib/api";

type Sessions = { active: number; current_expires_at: number };
export function AccountSettings({ user }: { user: User }) {
  const router = useRouter();
  const [sessions, setSessions] = useState<Sessions | null>(null);
  const [password, setPassword] = useState("");
  const [nextPassword, setNextPassword] = useState("");
  const [repeat, setRepeat] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [deleting, setDeleting] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const setMessage = useToast();
  useEffect(() => {
    api<Sessions>("/account/sessions").then(setSessions).catch((e) => setError(e.message));
  }, []);
  async function run(action: "password" | "revoke" | "export" | "delete") {
    setError(""); setMessage("");
    if (!password) { setError("Введите текущий пароль"); return; }
    if (action === "password" && nextPassword !== repeat) { setError("Новые пароли не совпадают"); return; }
    setBusy(true);
    try {
      if (action === "export") {
        const data = await post("/account/export", { password });
        const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
        const link = document.createElement("a"); link.href = url; link.download = "razryad-account.json";
        document.body.appendChild(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
        setMessage("Выгрузка скачана. Храните файл в защищённом месте: он содержит ваши данные.");
      } else if (action === "delete") {
        await api("/account", { method: "DELETE", body: JSON.stringify({ password, confirmation }) });
        for (const key of Object.keys(localStorage)) if (key.includes(user.id)) localStorage.removeItem(key);
        router.replace("/auth?deleted=1");
      } else {
        const result = await post<{ message: string }>(action === "password" ? "/account/password" : "/account/sessions/revoke", action === "password" ? { password, new_password: nextPassword } : { password });
        setMessage(result.message);
        setSessions(await api<Sessions>("/account/sessions"));
        setNextPassword(""); setRepeat("");
      }
      setPassword("");
    } catch (e) { setError((e as Error).message); }
    finally { setBusy(false); }
  }
  function changePassword(e: FormEvent) { e.preventDefault(); void run("password"); }
  return <>
    <PageHead eyebrow="ДОСТУП И ДАННЫЕ" title="Настройки аккаунта" text={user.email} />
    <div aria-live="polite">{error && <Notice error>{error}</Notice>}</div>
    <div className="rz-profile-grid">
      <form className="rz-panel rz-form" onSubmit={changePassword}>
        <h2>Пароль и сеансы</h2>
        <p className="rz-muted">Текущий пароль подтверждает смену доступа, выгрузку и удаление данных.</p>
        <Field label="Текущий пароль"><Input type="password" autoComplete="current-password" maxLength={128} required value={password} onChange={(e) => setPassword(e.target.value)} /></Field>
        <Field label="Новый пароль"><Input type="password" autoComplete="new-password" minLength={10} maxLength={128} required value={nextPassword} onChange={(e) => setNextPassword(e.target.value)} /></Field>
        <Field label="Повторите новый пароль"><Input type="password" autoComplete="new-password" minLength={10} maxLength={128} required value={repeat} onChange={(e) => setRepeat(e.target.value)} /></Field>
        <p className="rz-muted">Не менее 10 символов. При смене пароля остальные сеансы завершатся.</p>
        <Button className="rz-button" disabled={busy} type="submit">Изменить пароль</Button>
        {sessions && <p>Активных сеансов: {sessions.active}. Текущий действует до {date(sessions.current_expires_at)}.</p>}
        <Button className="rz-button secondary" disabled={busy || !sessions || sessions.active < 2} type="button" onClick={() => void run("revoke")}>Завершить остальные сеансы</Button>
      </form>
      <div className="rz-form">
        <section className="rz-panel rz-form">
          <h2>Копия ваших данных</h2>
          <p className="rz-muted">Профиль и связанные записи в формате JSON. Сначала введите текущий пароль в форме слева.</p>
          <Button className="rz-button secondary" disabled={busy} onClick={() => void run("export")}>Скачать мои данные</Button>
        </section>
        <section className="rz-panel rz-form">
          <h2>Удаление аккаунта</h2>
          <p className="rz-muted">Удалятся профиль, доступы и связанные записи. {user.role === "employer" ? "Также удалятся вакансии, задания и ответы на них." : "Также удалятся результаты тестов, отклики и решения практики."} Отменить действие нельзя.</p>
          <p className="rz-muted">Автоматические резервные копии хранятся семь дней. Удаление не отзывает уже скачанные другими участниками файлы.</p>
          {!deleting ? <Button className="rz-button secondary" disabled={busy} onClick={() => setDeleting(true)}>Удалить аккаунт…</Button> : <>
            <Field label="Введите УДАЛИТЬ"><Input autoComplete="off" value={confirmation} onChange={(e) => setConfirmation(e.target.value)} /></Field>
            <Button variant="destructive" disabled={busy || confirmation !== "УДАЛИТЬ" || !password} onClick={() => void run("delete")}>Удалить аккаунт навсегда</Button>
            <Button variant="ghost" disabled={busy} onClick={() => {setDeleting(false); setConfirmation("");}}>Отмена</Button>
          </>}
        </section>
      </div>
    </div>
  </>;
}
