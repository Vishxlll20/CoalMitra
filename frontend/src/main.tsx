import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { Toaster } from "sonner";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
      <Toaster
        position="bottom-right"
        toastOptions={{
          className: "!font-sans !text-[13px] !bg-navy-900 !text-paper !border-0",
          duration: 3200,
        }}
      />
    </BrowserRouter>
  </React.StrictMode>
);