import type { Metadata } from "next";
import { Vazirmatn } from "next/font/google";
import "./globals.css";

const vazir = Vazirmatn({
  subsets: ["arabic"],
  variable: "--font-vazir",
});

export const metadata: Metadata = {
  title: "مدیریت از راه دور اندروید",
  description: "Android Remote Device Manager",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fa" dir="rtl" className="dark">
      <body className={`${vazir.variable} min-h-screen bg-zinc-950 font-sans antialiased`}>
        {children}
      </body>
    </html>
  );
}
