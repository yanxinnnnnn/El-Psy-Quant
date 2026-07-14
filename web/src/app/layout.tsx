import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "El-Psy-Quant · Founder Workspace",
  description: "Local Founder paper-trading review workspace",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
