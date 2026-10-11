"use client";

import {
  createContext,
  useCallback,
  useContext,
  useRef,
  useState,
} from "react";
import { Toast } from "radix-ui";
import { CheckCircle, X } from "@phosphor-icons/react";

const ToastContext = createContext<(message: string) => void>(() => {});

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<{ id: number; message: string }[]>([]);
  const sequence = useRef(0);
  const notify = useCallback((message: string) => {
    if (!message.trim()) return;
    const item = { id: ++sequence.current, message };
    setItems((current) => [
      ...current.filter((v) => v.message !== message).slice(-2),
      item,
    ]);
  }, []);
  return (
    <ToastContext.Provider value={notify}>
      <Toast.Provider
        duration={6500}
        swipeDirection="right"
        label="Уведомление"
      >
        {children}
        {items.map((item) => (
          <Toast.Root
            key={item.id}
            className="rz-toast"
            type="background"
            onOpenChange={(open) => {
              if (!open)
                setItems((current) => current.filter((v) => v.id !== item.id));
            }}
          >
            <CheckCircle
              className="rz-toast-icon"
              size={24}
              weight="fill"
              aria-hidden
            />
            <Toast.Title className="rz-toast-title">{item.message}</Toast.Title>
            <Toast.Close
              className="rz-toast-close"
              aria-label="Закрыть уведомление"
            >
              <X size={18} />
            </Toast.Close>
          </Toast.Root>
        ))}
        <Toast.Viewport
          className="rz-toast-viewport"
          label="Уведомления (F8)"
        />
      </Toast.Provider>
    </ToastContext.Provider>
  );
}

export const useToast = () => useContext(ToastContext);
