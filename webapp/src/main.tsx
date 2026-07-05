import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import App from "./App";
import { USE_MOCK } from "./api/client";
import { queryClient } from "./api/queryClient";
import { startStreamBridge } from "./api/streamBridge";
import "./styles/index.css";

async function bootstrap() {
  if (USE_MOCK) {
    // 无后端时启用 MSW 网络层 mock；业务代码走同一条 fetch 路径
    const { worker } = await import("./api/mocks/browser");
    await worker.start({ onUnhandledRequest: "bypass", quiet: true });
  }
  // WS/mock 流 → Query 缓存 唯一桥
  startStreamBridge();

  ReactDOM.createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </QueryClientProvider>
    </React.StrictMode>,
  );
}

void bootstrap();
