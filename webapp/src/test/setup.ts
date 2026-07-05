/** vitest 全局 setup —— jest-dom 断言 + MSW node server（与 dev 共用同一套 handlers） */
import "@testing-library/jest-dom/vitest";
import { afterAll, afterEach, beforeAll } from "vitest";
import { cleanup } from "@testing-library/react";
import { setupServer } from "msw/node";
import { handlers } from "@/api/mocks/handlers";

export const server = setupServer(...handlers);

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => {
  cleanup(); // globals:false 下 RTL 不会自动注册 cleanup
  server.resetHandlers();
});
afterAll(() => server.close());
