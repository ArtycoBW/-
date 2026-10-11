"use client";
import { useRef } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
export function Modal({
  title,
  wide = false,
  className = "",
  children,
  onClose,
}: {
  title: string;
  wide?: boolean;
  className?: string;
  children: React.ReactNode;
  onClose: () => void;
}) {
  const returnFocus = useRef<HTMLElement | null>(null);
  const heading = useRef<HTMLHeadingElement | null>(null);
  return (
    <Dialog
      open
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <DialogContent
        className={`rz-dialog ${wide ? "rz-dialog-wide" : ""} ${className}`}
        aria-describedby={undefined}
        onOpenAutoFocus={(event) => {
          event.preventDefault();
          returnFocus.current = document.activeElement as HTMLElement;
          heading.current?.focus();
        }}
        onCloseAutoFocus={(event) => {
          event.preventDefault();
          returnFocus.current?.focus({ preventScroll: true });
        }}
      >
        <DialogHeader>
          <DialogTitle ref={heading} tabIndex={-1}>
            {title}
          </DialogTitle>
        </DialogHeader>
        <div className="rz-dialog-body">{children}</div>
      </DialogContent>
    </Dialog>
  );
}
