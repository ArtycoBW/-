"use client";
import { useEffect, useState } from "react";
import { LockKey } from "@phosphor-icons/react";
import { api, date } from "@/lib/api";
import { Notice } from "./ui";
type Grant = { company_id: string; company_name: string; created_at: number; reason: string };
export function ContactAccess() {
  const [grants, setGrants] = useState<Grant[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState("");
  useEffect(() => { api<Grant[]>("/profile/contact-grants").then(setGrants).catch(e => setError(e.message)); }, []);
  async function revoke(id: string) {
    setBusy(id); setError("");
    try {
      await api(`/profile/contact-grants/${id}`, { method: "DELETE" });
      setGrants(old => old.filter(x => x.company_id !== id));
      setMessage("Доступ отозван. Компания больше не получает контакт через платформу.");
    } catch (e) { setError((e as Error).message); }
    finally { setBusy(""); }
  }
  return <section className="rz-panel rz-contact-access"><LockKey size={25} /><h2>Доступ к контактам</h2>
    <p className="rz-muted">Вы решаете, каким компаниям доступен ваш контакт.</p>
    {error && <Notice error>{error}</Notice>}{message && <Notice>{message}</Notice>}
    {grants.length ? grants.map(grant => <div className="rz-access-row" key={grant.company_id}><div><strong>{grant.company_name}</strong><small>С {date(grant.created_at)}</small></div><button className="rz-button small" disabled={!!busy} onClick={() => revoke(grant.company_id)}>{busy === grant.company_id ? "Отзываем…" : "Отозвать доступ"}</button></div>) : <p className="rz-access-empty">Сейчас ни у одной компании нет доступа.</p>}
    <small className="rz-muted">Отзыв прекращает дальнейшую выдачу контакта. Уже сохранённые компанией данные платформа удалить не может.</small>
  </section>;
}
