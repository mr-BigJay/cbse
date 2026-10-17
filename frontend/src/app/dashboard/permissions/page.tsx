"use client";

import { Card } from "@/components/ui/card";

export default function PermissionsPage() {
  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">مجوزهای دستگاه</h2>
      <Card className="prose prose-invert max-w-none text-sm text-zinc-300">
        <p>
          عامل اندروید فقط مجوزهای لازم برای قابلیت‌های فعال را درخواست می‌کند. موقعیت، SMS،
          اعلان‌ها و Device Admin هر کدام با رضایت صریح کاربر فعال می‌شوند.
        </p>
        <ul className="mt-3 list-disc pr-5">
          <li>موقعیت: ACCESS_FINE_LOCATION و در صورت نیاز BACKGROUND</li>
          <li>SMS: RECEIVE_SMS فقط برای کانال پشتیبان</li>
          <li>قفل دستگاه: Device Admin یا Device Owner</li>
        </ul>
      </Card>
    </div>
  );
}
