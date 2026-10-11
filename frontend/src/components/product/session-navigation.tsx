"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { PillButton, type PillButtonProps } from "@/components/ui/pill-button";

type SessionStatus = "loading" | "authenticated" | "guest" | "unavailable";

function useSessionStatus(): SessionStatus {
  const pathname = usePathname();
  const [status, setStatus] = useState<SessionStatus>("loading");
  useEffect(() => {
    let active = true;
    let request = 0;
    async function check() {
      const current = ++request;
      try {
        await api("/auth/me", { cache: "no-store" });
        if (active && current === request) setStatus("authenticated");
      } catch (error) {
        if (active && current === request)
          setStatus(error instanceof ApiError && error.status === 401 ? "guest" : "unavailable");
      }
    }
    void check();
    window.addEventListener("focus", check);
    return () => { active = false; window.removeEventListener("focus", check); };
  }, [pathname]);
  return status;
}

// A failed connection is not proof of logout. /app can retry the session check.
export function SessionReturnLink({ className }: { className?: string }) {
  const status = useSessionStatus();
  return <Link className={className} href={status === "guest" ? "/" : "/app"}>
    {status === "guest" ? "← На главную" : status === "authenticated" ? "← В кабинет" : "← Назад"}
  </Link>;
}

export function SessionActionLink({ className }: { className?: string }) {
  const status = useSessionStatus();
  return <Link className={className} href={status === "guest" ? "/auth?mode=register" : "/app"}>
    {status === "guest" ? "Создать профиль" : "В кабинет"}
  </Link>;
}

export function SessionNavButton(props: PillButtonProps) {
  const status = useSessionStatus();
  return <PillButton {...props} href={status === "guest" ? props.href : "/app"}>
    {status === "guest" ? props.children : "В кабинет"}
  </PillButton>;
}
