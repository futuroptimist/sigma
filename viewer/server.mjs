import { createServer } from "http";
import { createReadStream, statSync } from "fs";
import { isAbsolute, join, normalize, relative, resolve } from "path";
import { fileURLToPath } from "url";

const __dirname = fileURLToPath(new URL("./", import.meta.url));
const docsRoot = resolve(__dirname, "../docs");
const port = Number(process.env.PORT ?? 4173);

function isPathInside(basePath, targetPath) {
  const relativeToBase = relative(basePath, targetPath);
  return (
    relativeToBase === "" ||
    (!relativeToBase.startsWith("..") && !isAbsolute(relativeToBase))
  );
}

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
  const normalizedPath = normalize(urlPath);
  const relativePath = normalizedPath.startsWith("/")
    ? normalizedPath.slice(1)
    : normalizedPath;
  const resolvedPath = resolve(docsRoot, relativePath);

  if (!isPathInside(docsRoot, resolvedPath)) {
    res.writeHead(403, { "Content-Type": "text/plain" });
    res.end("Forbidden\n");
    return;
  }

  const candidates = [resolvedPath, join(resolvedPath, "index.html")];

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
