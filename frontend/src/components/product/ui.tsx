"use client";
import { ReactNode } from "react";
import Link from "next/link";
export function Mark() {
  return (
    <span className="rz-mark" aria-hidden="true">
      ↗
    </span>
  );
}
export function Brand() {
  return (
    <Link className="rz-brand" href="/">
      <Mark />
      <span>
        разряд<span className="rz-brand-dot">.</span>
      </span>
    </Link>
  );
}
export function Tag({
  children,
  tone = "",
}: {
  children: ReactNode;
  tone?: string;
}) {
  return <span className={`rz-tag ${tone}`}>{children}</span>;
}
export function Empty({
  title,
  children,
}: {
  title: string;
  children?: ReactNode;
}) {
  return (
    <div className="rz-empty">
      <span aria-hidden="true">↗</span>
      <h3>{title}</h3>
      <p>{children}</p>
    </div>
  );
}
export function Notice({
  children,
  error = false,
}: {
  children: ReactNode;
  error?: boolean;
}) {
  return (
    <div
      className={`rz-notice ${error ? "error" : ""}`}
      role={error ? "alert" : "status"}
    >
      {children}
    </div>
  );
}
export function Field({
  label,
  children,
  hint,
}: {
  label: string;
  children: ReactNode;
  hint?: string;
}) {
  return (
    <div className="rz-field">
      <label><span>{label}</span>{children}</label>
      {hint && <small>{hint}</small>}
    </div>
  );
}
export function SelectSpec({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)}>
      <option value="backend">Бэкенд-разработка</option>
      <option value="frontend">Фронтенд-разработка</option>
    </select>
  );
}
export function SelectGrade({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)}>
      <option value="junior">Начальный (Junior)</option>
      <option value="middle">Средний (Middle)</option>
      <option value="senior">Старший (Senior)</option>
    </select>
  );
}
export function Skills({ items }: { items: string[] }) {
  return (
    <div className="rz-tags">
      {items.map((x) => (
        <Tag key={x}>{x}</Tag>
      ))}
    </div>
  );
}
