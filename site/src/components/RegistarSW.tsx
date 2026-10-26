"use client";

import { useEffect } from "react";

/** Service worker: permite abrir o check-in e a app do sócio sem rede. */
export function RegistarSW() {
  useEffect(() => {
    if ("serviceWorker" in navigator && process.env.NODE_ENV === "production") {
      navigator.serviceWorker.register("/sw.js").catch(() => {});
    }
  }, []);
  return null;
}
