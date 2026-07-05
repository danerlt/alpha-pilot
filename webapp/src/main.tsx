import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { USE_MOCK } from "./api/client";
import "./styles/index.css";

async function bootstrap() {
  if (USE_MOCK) {
    // 无后端时启用 MSW 网络层 mock；业务代码走同一条 fetch 路径
    const { worker } = await import("./api/mocks/browser");
    await worker.start({ onUnhandledRequest: "bypass" });
  }
  ReactDOM.createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </React.StrictMode>,
  );
}

void bootstrap();
