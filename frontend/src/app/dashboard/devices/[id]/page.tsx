"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { api, capabilityLabel, commandStatusLabel, Device, Command, LocationPoint } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

const COMMAND_TYPES = ["STATUS", "LOCATE", "ALARM", "LOCK", "APP_LIST", "SYNC_STATUS"];

export default function DeviceDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [device, setDevice] = useState<Device | null>(null);
  const [commands, setCommands] = useState<Command[]>([]);
  const [locations, setLocations] = useState<LocationPoint[]>([]);
  const [message, setMessage] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setDevice(await api.device(id));
    setCommands(await api.commands(id));
    setLocations(await api.locations(id));
  }, [id]);

  useEffect(() => {
    refresh().catch(console.error);
    const t = setInterval(() => refresh().catch(console.error), 5000);
    return () => clearInterval(t);
  }, [refresh]);

  async function sendCommand(type: string) {
    setMessage(null);
    try {
      const cmd = await api.createCommand(id, type, crypto.randomUUID());
      setMessage(`فرمان ${type} ایجاد شد — وضعیت: ${commandStatusLabel(cmd.status)}`);
      await refresh();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "خطا");
    }
  }

  if (!device) return <p>در حال بارگذاری...</p>;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">{device.name}</h2>
        <p className="text-sm text-zinc-400">
          {device.manufacturer} {device.model} · حالت {device.mode}
        </p>
      </div>

      <Card>
        <h3 className="mb-3 font-semibold">کنترل از راه دور</h3>
        <p className="mb-3 text-xs text-zinc-500">
          موفقیت فقط پس از تأیید عامل اندروید (وضعیت completed) نمایش داده می‌شود.
        </p>
        <div className="flex flex-wrap gap-2">
          {COMMAND_TYPES.map((type) => {
            const cap = device.capabilities[type] || "unsupported";
            const disabled = cap === "unsupported";
            return (
              <Button
                key={type}
                size="sm"
                variant={disabled ? "outline" : "default"}
                disabled={disabled || device.status !== "active"}
                onClick={() => sendCommand(type)}
                title={capabilityLabel(cap)}
              >
                {type}
              </Button>
            );
          })}
        </div>
        {message && <p className="mt-3 text-sm text-zinc-300">{message}</p>}
      </Card>

      <Card>
        <h3 className="mb-2 font-semibold">آخرین موقعیت</h3>
        {locations[0] ? (
          <p className="text-sm">
            {locations[0].latitude.toFixed(5)}, {locations[0].longitude.toFixed(5)} —{" "}
            {new Date(locations[0].recorded_at).toLocaleString("fa-IR")}
          </p>
        ) : (
          <p className="text-sm text-zinc-500">موقعیتی گزارش نشده است.</p>
        )}
      </Card>

      <Card>
        <h3 className="mb-2 font-semibold">تاریخچه فرمان</h3>
        <ul className="space-y-2 text-sm">
          {commands.map((c) => (
            <li key={c.id} className="flex justify-between border-b border-zinc-800 py-2">
              <span>
                {c.type} — {commandStatusLabel(c.status)}
              </span>
              <span className="text-zinc-500">{new Date(c.created_at).toLocaleString("fa-IR")}</span>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
