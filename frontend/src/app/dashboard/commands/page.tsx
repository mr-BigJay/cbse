"use client";

import { useEffect, useState } from "react";
import { api, commandStatusLabel, Command } from "@/lib/api";
import { Card } from "@/components/ui/card";

export default function CommandsPage() {
  const [commands, setCommands] = useState<Command[]>([]);

  useEffect(() => {
    const load = () => api.commands().then(setCommands).catch(console.error);
    load();
    const t = setInterval(load, 4000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">فرمان‌های از راه دور</h2>
      <Card>
        <ul className="divide-y divide-zinc-800 text-sm">
          {commands.map((c) => (
            <li key={c.id} className="flex flex-wrap justify-between gap-2 py-3">
              <span>
                {c.type} · دستگاه {c.device_id.slice(0, 8)}
              </span>
              <span className="text-emerald-300">{commandStatusLabel(c.status)}</span>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
