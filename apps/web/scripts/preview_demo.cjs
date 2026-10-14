// Lightweight local preview of the same React page when Next cannot fit in RAM.
// Generated files remain under ignored out/; this is not a production server.
const fs = require("node:fs");
const path = require("node:path");
const http = require("node:http");
const ts = require("typescript");
const { webpack } = require("next/dist/compiled/webpack/webpack");
const web = path.resolve(__dirname, "..");
const output = path.join(web, "out", "demo");
fs.mkdirSync(path.join(output, "src", "app"), { recursive: true });
fs.mkdirSync(path.join(output, "src", "data"), { recursive: true });
fs.writeFileSync(path.join(output, "src", "app", "page.js"), ts.transpileModule(
  fs.readFileSync(path.join(web, "src", "app", "page.tsx"), "utf8"),
  { compilerOptions: { jsx: ts.JsxEmit.ReactJSX, module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2020 } },
).outputText);
fs.copyFileSync(path.join(web, "src", "data", "mv-hondius.snapshot.json"), path.join(output, "src", "data", "mv-hondius.snapshot.json"));
fs.copyFileSync(path.join(web, "src", "app", "globals.css"), path.join(output, "styles.css"));
fs.writeFileSync(path.join(output, "entry.js"), 'import { createRoot } from "react-dom/client"; import { createElement } from "react"; import Page from "./src/app/page.js"; createRoot(document.getElementById("root")).render(createElement(Page));');
fs.writeFileSync(path.join(output, "index.html"), '<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MV Hondius · OETI · Demo retrospectiva</title><link rel="stylesheet" href="/styles.css"></head><body><div id="root"></div><script src="/bundle.js" defer></script></body></html>');
const compiler = webpack({
  mode: "production", entry: path.join(output, "entry.js"), devtool: false,
  output: { path: output, filename: "bundle.js" },
  resolve: { extensions: [".js", ".json"], modules: [path.resolve(web, "../../node_modules"), "node_modules"] },
  optimization: { minimize: false }, parallelism: 1, cache: false,
});
compiler.run((error, stats) => {
  compiler.close(() => {});
  if (error || stats.hasErrors()) {
    console.error(error ? error.message : stats.toString({ all: false, errors: true }));
    process.exitCode = 1; return;
  }
  console.log("Demo bundle compiled successfully.");
  const standalone = fs.readFileSync(path.join(output, "index.html"), "utf8")
    .replace('<link rel="stylesheet" href="/styles.css">', () => `<style>${fs.readFileSync(path.join(output, "styles.css"), "utf8")}</style>`)
    .replace('<script src="/bundle.js" defer></script>', () => `<script>${fs.readFileSync(path.join(output, "bundle.js"), "utf8").replace(/<\/script/gi, '<\\/script')}</script>`);
  fs.writeFileSync(path.join(output, "ficha-mv-hondius.html"), standalone);
  fs.writeFileSync(path.join(output, "index.html"), standalone);
  if (process.argv.includes("--build-only")) return;
  const allowed = { "/": ["index.html", "text/html"], "/ficha-mv-hondius.html": ["ficha-mv-hondius.html", "text/html"], "/styles.css": ["styles.css", "text/css"], "/bundle.js": ["bundle.js", "text/javascript"] };
  const server = http.createServer((request, response) => {
    const asset = allowed[new URL(request.url, "http://127.0.0.1").pathname];
    if (!asset || !["GET", "HEAD"].includes(request.method)) { response.writeHead(404); response.end(); return; }
    response.writeHead(200, { "Content-Type": `${asset[1]}; charset=utf-8`, "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" });
    response.end(request.method === "HEAD" ? undefined : fs.readFileSync(path.join(output, asset[0])));
  });
  server.listen(3015, "127.0.0.1", () => console.log("Local: http://127.0.0.1:3015"));
  server.on("error", error => { console.error(error.code); process.exitCode = 1; });
  process.on("SIGINT", () => server.close(() => process.exit(0)));
});
