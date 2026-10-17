"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const links = [
  { href: "/dashboard", label: "نمای کلی" },
  { href: "/dashboard/devices", label: "دستگاه‌ها" },
  { href: "/dashboard/map", label: "نقشه" },
  { href: "/dashboard/commands", label: "فرمان‌ها" },
  { href: "/dashboard/enrollment", label: "ثبت‌نام دستگاه" },
  { href: "/dashboard/sms", label: "پشتیبان SMS" },
  { href: "/dashboard/permissions", label: "مجوزها" },
  { href: "/dashboard/security", label: "امنیت" },
  { href: "/dashboard/audit", label: "گزارش ممیزی" },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="hidden w-64 shrink-0 border-l border-zinc-800 bg-zinc-950 p-4 md:block">
      <div className="mb-8">
        <h1 className="text-lg font-bold text-emerald-400">مدیریت از راه دور</h1>
        <p className="text-xs text-zinc-500">Android Remote Device Manager</p>
      </div>
      <nav className="flex flex-col gap-1">
        {links.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className={cn(
              "rounded-md px-3 py-2 text-sm transition-colors",
              pathname === link.href
                ? "bg-emerald-600/20 text-emerald-300"
                : "text-zinc-300 hover:bg-zinc-900",
            )}
          >
            {link.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
