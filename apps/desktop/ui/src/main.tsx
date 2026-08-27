/** Console desktop VERA : l’état et le preview précèdent toujours l’action project-local. */
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { DesktopConsole } from "./DesktopConsole";
import "./styles.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <DesktopConsole />
  </StrictMode>,
);
