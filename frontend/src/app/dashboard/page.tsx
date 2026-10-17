"use client";

import { useEffect, useState } from "react";
import { api, Device } from "@/lib/api";
import { Card } from "@/components/ui/card";

export default function OverviewPage() {
  const [devices, setDevices] = useState<Device[]>([]);

  useEffect(() => {
    api.devices().then(setDevices).catch(console.error);
  }, []);

  const online = devices.filter((d) => d.online).length;
  const pending = devices.filter((d) => d.status === "pending_approval").length;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">نمای کلی</h2>
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <p className="text-sm text-zinc-400">کل دستگاه‌ها</p>
          <p className="text-3xl font-bold">{devices.length}</p>
        </Card>
        <Card>
          <p className="text-sm text-zinc-400">آنلاین</p>
          <p className="text-3xl font-bold text-emerald-400">{online}</p>
        </Card>
        <Card>
          <p className="text-sm text-zinc-400">در انتظار تأیید</p>
          <p className="text-3xl font-bold text-amber-400">{pending}</p>
        </Card>
      </div>
    </div>
  );
}
