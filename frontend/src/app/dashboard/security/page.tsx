"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function SecurityPage() {
  const [days, setDays] = useState(30);

  useEffect(() => {
    api.settings().then((s) => setDays(s.location_retention_days));
  }, []);

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">تنظیمات امنیتی</h2>
      <Card className="space-y-3">
        <label className="text-sm text-zinc-400">نگهداری موقعیت (روز)</label>
        <Input
          type="number"
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
        />
        <Button onClick={() => api.updateSettings(days)}>ذخیره</Button>
        <p className="text-xs text-zinc-500">
          MFA از مسیر API (`/api/v1/auth/mfa/setup`) قابل فعال‌سازی است.
        </p>
      </Card>
    </div>
  );
}
