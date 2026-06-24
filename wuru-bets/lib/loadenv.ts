// Carga .env ANTES de cualquier import que lea process.env (lib/db).
// Debe importarse como PRIMERA línea en los scripts CLI.
try { (process as unknown as { loadEnvFile?: (p?: string) => void }).loadEnvFile?.(".env"); } catch {}
