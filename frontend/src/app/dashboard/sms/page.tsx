"use client";

import { useEffect, useState } from "react";
import { api, Device } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function SmsPage() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [deviceId, setDeviceId] = useState("");
  const [numbers, setNumbers] = useState("");

  useEffect(() => {
    api.devices().then((d) => {
      setDevices(d);
      if (d[0]) setDeviceId(d[0].id);
    });
  }, []);

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">پشتیبان SMS</h2>
      <Card className="space-y-3">
        <p className="text-sm text-zinc-400">
          فرمت: <code className="text-emerald-300">ARDM v1:STATUS:exp:nonce:hmac</code> — کلید HMAC در
          زمان ثبت‌نام در دستگاه ذخیره می‌شود. فرمان‌های مخرب از طریق SMS در نسخه اول مجاز نیستند.
        </p>
        <select
          className="h-10 w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 text-sm"
          value={deviceId}
          onChange={(e) => setDeviceId(e.target.value)}
        >
          {devices.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name}
            </option>
          ))}
        </select>
        <Input
          placeholder="شماره‌های مجاز (با کاما)"
          value={numbers}
          onChange={(e) => setNumbers(e.target.value)}
        />
        <Button
          onClick={async () => {
            const phone_numbers = numbers.split(",").map((n) => n.trim()).filter(Boolean);
            await api.updateSmsSenders(deviceId, phone_numbers);
          }}
        >
          ذخیره فرستندگان مجاز
        </Button>
      </Card>
    </div>
  );
}
