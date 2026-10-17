"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, Device } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export default function DevicesPage() {
  const [devices, setDevices] = useState<Device[]>([]);

  async function load() {
    setDevices(await api.devices());
  }

  useEffect(() => {
    load().catch(console.error);
  }, []);

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">دستگاه‌های ثبت‌شده</h2>
      <div className="grid gap-3">
        {devices.map((d) => (
          <Card key={d.id} className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <div>
              <Link href={`/dashboard/devices/${d.id}`} className="font-semibold text-emerald-300 hover:underline">
                {d.name}
              </Link>
              <p className="text-sm text-zinc-400">
                {d.manufacturer} {d.model} · Android {d.android_version}
              </p>
              <p className="text-xs text-zinc-500">
                وضعیت: {d.status} · {d.online ? "آنلاین" : "آفلاین"} · باتری:{" "}
                {d.battery_level ?? "—"}%
              </p>
            </div>
            {d.status === "pending_approval" && (
              <Button
                size="sm"
                onClick={async () => {
                  await api.approveDevice(d.id);
                  await load();
                }}
              >
                تأیید ثبت‌نام
              </Button>
            )}
          </Card>
        ))}
        {!devices.length && <p className="text-zinc-400">هنوز دستگاهی ثبت نشده است.</p>}
      </div>
    </div>
  );
}
