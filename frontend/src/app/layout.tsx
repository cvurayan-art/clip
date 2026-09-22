import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Video Clipper — Local Crayo-Style Personal App",
  description: "Locally powered AI video clipper with NVIDIA GPU acceleration, smart 9:16 subject tracking, and viral moment detection.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background antialiased flex flex-col selection:bg-primary selection:text-white">
        {children}
      </body>
    </html>
  );
}
