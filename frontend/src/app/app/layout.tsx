import { Suspense } from "react";
import { Dashboard } from "@/views/product/dashboard";

export default function WorkspaceLayout({ children }: { children: React.ReactNode }) {
  return <><Suspense><Dashboard /></Suspense>{children}</>;
}
