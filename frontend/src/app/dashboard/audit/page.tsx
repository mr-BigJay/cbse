"use client";

import { useEffect, useState } from "react";
import { api, AuditEntry } from "@/lib/api";
import { Card } from "@/components/ui/card";

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditEntry[]>([]);

  useEffect(() => {
    api.audit().then(setLogs).catch(console.error);
  }, []);

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">گزارش ممیزی</h2>
      <Card>
        <ul className="divide-y divide-zinc-800 text-sm">
          {logs.map((l) => (
            <li key={l.id} className="py-2">
              <span className="text-emerald-300">{l.action}</span>
              <span className="mx-2 text-zinc-600">·</span>
              <span className="text-zinc-500">{new Date(l.created_at).toLocaleString("fa-IR")}</span>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
