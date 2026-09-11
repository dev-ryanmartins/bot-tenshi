// Ensure window.fetch has both a getter and setter to prevent "Cannot set property fetch" errors
try {
  if (typeof window !== "undefined" && window.fetch) {
    let _f = window.fetch.bind(window);
    Object.defineProperty(window, "fetch", {
      configurable: true,
      enumerable: true,
      get: () => _f,
      set: (val) => {
        _f = typeof val === "function" ? val.bind(window) : val;
      },
    });
  }
} catch {
  // Ignore descriptor configuration issues
}

import { createRoot } from "react-dom/client";
import App from "./App";
import "./index.css";

createRoot(document.getElementById("root")!).render(<App />);
