"use client";
import { useEffect, useState } from "react";
import { api, post, type Profile } from "@/lib/api";
import { Button } from "@/components/ui/button";

type Provider = { enabled: boolean; mode: string; label: string };

export function FspConnection({ profile, onUpdated }: { profile: Profile; onUpdated: (p: Profile) => void }) {
  const [provider, setProvider] = useState<Provider | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  useEffect(() => {
    api<Provider>("/integrations/fsp/oidc/status").then(setProvider).catch((e: Error) => setNotice(e.message));
  }, []);
  async function connect() {
    setBusy(true); setNotice("");
    try {
      if (provider?.enabled) {
        const result = await post<{ authorization_url: string }>("/integrations/fsp/oidc/start", {});
        window.location.assign(result.authorization_url);
        return;
      }
      onUpdated(await post<Profile>("/integrations/fsp", { participant_id: "DEMO-FSP-2026" }));
      setNotice("Подключён демонстрационный реестр.");
    } catch (e) { setNotice((e as Error).message); }
    setBusy(false);
  }
  return <section className="rz-panel">
    <div className="rz-section-title"><h2>Профиль ФСП</h2><span className="rz-muted">{provider?.mode === "external" ? "Внешний провайдер" : "Учебный стенд"}</span></div>
    {profile.fsp_id && <p role="status">ФСП ID связан с профилем</p>}
    {profile.achievements.length ? profile.achievements.map((a) => <div className="rz-achievement" key={a.id}>
      <b>♜ {a.place} место</b><p>{a.title}</p><small>{a.discipline} · {a.date}</small>
    </div>) : <p className="rz-muted">Нет связанной истории. Это не мешает получать предложения.</p>}
    <div className="rz-actions">
      <Button className="rz-button" disabled={busy || !provider || !!profile.fsp_id} onClick={connect}>
        {provider?.enabled ? provider.mode === "local" ? "Войти в локальный ФСП ID" : "Связать ФСП ID" : "Связать демо-ID"}
      </Button>
      {profile.fsp_id && <Button className="rz-text-link" disabled={busy} onClick={async () => {
        setBusy(true);
        try { onUpdated(await api<Profile>("/integrations/fsp", { method: "DELETE" })); setNotice("Профиль ФСП отвязан."); }
        catch (e) { setNotice((e as Error).message); }
        finally { setBusy(false); }
      }}>Отвязать</Button>}
    </div>
    {notice && <p role="status">{notice}</p>}
    <small className="rz-muted">{provider?.mode === "local" ? "Вход через локальный Keycloak. Достижения учебные; доступа к реестру Федерации нет." : "Официальный доступ к данным Федерации пока не подтверждён."}</small>
  </section>;
}
