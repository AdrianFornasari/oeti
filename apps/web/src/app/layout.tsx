import type { ReactNode } from "react";

export const metadata = {
  title: "One Health Emerging Threat Intelligence",
  description: "Argentina-first One Health epidemic intelligence MVP",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="es">
      <body style={{ margin: 0, fontFamily: "Arial, sans-serif", background: "#071820", color: "#eaf4f2" }}>
        {children}
      </body>
    </html>
  );
}
