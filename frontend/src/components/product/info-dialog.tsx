"use client";
import { useState, type ReactNode } from "react";
import { Modal } from "./modal";
import { MethodologyView } from "@/views/product/methodology";
import { PrivacyView } from "@/views/product/privacy";
import { Button } from "@/components/ui/button";

export function InfoDialog({
  kind,
  onClose,
}: {
  kind: "privacy" | "methodology";
  onClose: () => void;
}) {
  return (
    <Modal
      wide
      title={kind === "privacy" ? "Приватность данных" : "Как работает подбор"}
      onClose={onClose}
    >
      {kind === "privacy" ? (
        <PrivacyView embedded />
      ) : (
        <MethodologyView embedded />
      )}
    </Modal>
  );
}
export function InfoLink({
  kind,
  children,
  className = "rz-text-link",
}: {
  kind: "privacy" | "methodology";
  children: ReactNode;
  className?: string;
}) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <Button
        variant="ghost"
        className={className}
        onClick={() => setOpen(true)}
      >
        {children}
      </Button>
      {open && <InfoDialog kind={kind} onClose={() => setOpen(false)} />}
    </>
  );
}
