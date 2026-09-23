import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.jsx";
import { BrowserRouter } from "react-router-dom";
import { registerSW } from "virtual:pwa-register";
import { HelpPointStatusProvider } from "./context/HelpPointStatusContext";

registerSW({
  immediate: true
});

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <BrowserRouter>
      <HelpPointStatusProvider>
        <App />
      </HelpPointStatusProvider>
    </BrowserRouter>
  </StrictMode>
);