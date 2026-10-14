import type { ReactNode } from "react";
import "./globals.css";

export const metadata = {
  title: "MV Hondius · OETI · Demo retrospectiva",
  description: "Ficha local de evidencia: cinco señales y tres relaciones registradas de MV Hondius.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="es">
      <body>
        {children}
      </body>
    </html>
  );
}
