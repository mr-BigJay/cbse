"use client";

import { Sidebar } from "@/components/sidebar";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  useEffect(() => {
    if (!localStorage.getItem("access_token")) {
      router.replace("/login");
    }
  }, [router]);

  return (
    <div className="flex min-h-screen">
      <main className="flex-1 p-4 md:p-6">{children}</main>
      <Sidebar />
    </div>
  );
}
