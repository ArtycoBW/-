"use client";
import { useState } from "react";
export function PageHead({
  eyebrow,
  title,
  text,
  action,
}: {
  eyebrow: string;
  title: string;
  text: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="rz-pagehead">
      <div>
        <p className="rz-eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        <p className="rz-muted">{text}</p>
      </div>
      {action}
    </div>
  );
}
export function useMessage() {
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  return { error, setError, message, setMessage, busy, setBusy };
}
