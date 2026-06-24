import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Wuru Bets — Paper Trading",
  description: "Modelo Wuru: value betting con paper trading, Kelly y CLV",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
