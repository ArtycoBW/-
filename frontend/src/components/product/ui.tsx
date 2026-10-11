"use client";
import { specializations } from "@/lib/taxonomy";
import { ReactNode } from "react";
import Link from "next/link";
import Image from "next/image";
import { AppSelect } from "./controls";
import { Badge } from "@/components/ui/workspace/badge";
import { Tray } from "@phosphor-icons/react";
export function Mark() {
  return (
    <span className="rz-mark" aria-hidden="true">
      <Image src="/brand/mark.svg" alt="" width={40} height={40} />
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
  return (
    <Badge variant="outline" className={`rz-tag ${tone}`}>
      {children}
    </Badge>
  );
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
      <span className="rz-empty-icon" aria-hidden="true">
        <Tray size={26} />
      </span>
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
      <label>
        <span>{label}</span>
        {children}
      </label>
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
    <AppSelect value={value} onChange={(e) => onChange(e.target.value)}>
      {specializations.map((spec) => <option key={spec.id} value={spec.id}>{spec.name}</option>)}
    </AppSelect>
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
    <AppSelect value={value} onChange={(e) => onChange(e.target.value)}>
      <option value="junior">Начальный (Junior)</option>
      <option value="middle">Средний (Middle)</option>
      <option value="senior">Старший (Senior)</option>
    </AppSelect>
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
