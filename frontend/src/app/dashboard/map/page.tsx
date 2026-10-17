"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/card";

const DeviceMap = dynamic(
  () => import("@/components/device-map").then((m) => m.DeviceMap),
  { ssr: false },
);

export default function MapPage() {
  const [points, setPoints] = useState<{ lat: number; lng: number; label: string }[]>([]);

  useEffect(() => {
    async function load() {
      const devices = await api.devices();
      const pts: { lat: number; lng: number; label: string }[] = [];
      for (const d of devices) {
        const locs = await api.locations(d.id);
        if (locs[0]) {
          pts.push({
            lat: locs[0].latitude,
            lng: locs[0].longitude,
            label: d.name,
          });
        }
      }
      setPoints(pts);
    }
    load().catch(console.error);
  }, []);

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">نقشه دستگاه‌ها</h2>
      <Card className="overflow-hidden p-0">
        <DeviceMap points={points} />
      </Card>
    </div>
  );
}
