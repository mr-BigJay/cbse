"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export default function EnrollmentPage() {
  const [code, setCode] = useState<string | null>(null);
  const [expires, setExpires] = useState<string | null>(null);

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">ثبت‌نام دستگاه</h2>
      <Card>
        <p className="mb-4 text-sm text-zinc-400">
          کد یک‌بارمصرف را در اپ اندروید وارد کنید. پس از ثبت، دستگاه را از فهرست تأیید کنید.
        </p>
        <Button
          onClick={async () => {
            const res = await api.createEnrollmentCode();
            setCode(res.code);
            setExpires(res.expires_at);
          }}
        >
          ایجاد کد ثبت‌نام
        </Button>
        {code && (
          <div className="mt-4 rounded-md bg-zinc-900 p-4">
            <p className="text-xs text-zinc-500">کد (فقط یک‌بار نمایش داده می‌شود)</p>
            <p className="break-all font-mono text-lg text-emerald-300">{code}</p>
            <p className="mt-2 text-xs text-zinc-500">
              انقضا: {expires ? new Date(expires).toLocaleString("fa-IR") : ""}
            </p>
          </div>
        )}
      </Card>
    </div>
  );
}
