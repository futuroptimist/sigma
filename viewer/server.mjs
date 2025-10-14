import { createServer } from "http";
import { createReadStream, statSync } from "fs";
import { join, normalize, resolve } from "path";
import { fileURLToPath } from "url";

const __dirname = fileURLToPath(new URL("./", import.meta.url));
const docsRoot = resolve(__dirname, "../docs");
const port = Number(process.env.PORT ?? 4173);

function sendFile(res, filePath) {
  try {
    const stat = statSync(filePath);
    if (stat.isDirectory()) {
      return false;
    }
    res.writeHead(200, { "Content-Length": stat.size });
    createReadStream(filePath).pipe(res);
    return true;
  } catch (err) {
    return false;
  }
}

const server = createServer((req, res) => {
  const urlPath = req.url?.split("?")[0] ?? "/";
  const safePath = normalize(urlPath).replace(/^\.\.(\\|\/|$)/, "");
  const candidates = [
    join(docsRoot, safePath),
    join(docsRoot, safePath, "index.html"),
  ];

  for (const candidate of candidates) {
    if (sendFile(res, candidate)) {
      return;
    }
  }

  res.writeHead(404, { "Content-Type": "text/plain" });
  res.end("Not found\n");
});

server.listen(port, () => {
  console.log(`[viewer] Serving docs from ${docsRoot} on http://localhost:${port}`);
});
