/** Document Upload — Phase I-2A Import Boundary。 */

import { useCallback, useState } from "react";
import { Link } from "react-router-dom";
import type { ImportResponse } from "../api/types";

export default function DocumentUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<ImportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);

  const handleFile = useCallback((f: File) => {
    setFile(f);
    setResult(null);
    setError(null);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const f = e.dataTransfer.files[0];
      if (f) handleFile(f);
    },
    [handleFile],
  );

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch("/api/documents/import", {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        const body = await res.text().catch(() => "");
        throw new Error(`Import failed (${res.status}): ${body}`);
      }
      const data: ImportResponse = await res.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-ink">Import Document</h1>

      {/* Drop zone */}
      <div
        className={`rounded-lg border-2 border-dashed p-12 text-center transition-colors ${
          dragOver
            ? "border-primary bg-blue-50"
            : "border-gray-300 bg-white"
        }`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
      >
        {file ? (
          <div className="space-y-2">
            <p className="text-lg font-medium text-ink">{file.name}</p>
            <p className="text-sm text-gray-500">
              {(file.size / 1024).toFixed(1)} KB
            </p>
            <button
              onClick={() => setFile(null)}
              className="text-sm text-gray-400 hover:text-gray-600"
            >
              Remove
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            <p className="text-lg text-gray-500">
              Drag & drop a PDF or DOCX file here
            </p>
            <p className="text-sm text-gray-400">or</p>
            <label className="inline-block cursor-pointer rounded-pill bg-primary px-6 py-2 text-sm font-medium text-white hover:bg-blue-700">
              Browse files
              <input
                type="file"
                accept=".pdf,.docx"
                className="hidden"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) handleFile(f);
                }}
              />
            </label>
          </div>
        )}
      </div>

      {/* Upload button */}
      {file && !result && (
        <button
          onClick={handleUpload}
          disabled={uploading}
          className="rounded-pill bg-ink px-8 py-3 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50"
        >
          {uploading ? "Importing..." : "Import Document"}
        </button>
      )}

      {/* Error */}
      {error && (
        <div className="rounded-lg bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="rounded-lg bg-white p-6 shadow-sm space-y-4">
          <h2 className="text-lg font-medium text-ink">
            {result.is_new ? "Document Imported" : "Document Already Exists"}
          </h2>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">File</span>
              <p className="font-mono">{result.file_name}</p>
            </div>
            <div>
              <span className="text-gray-500">SHA256</span>
              <p className="font-mono text-xs break-all">{result.sha256}</p>
            </div>
            <div>
              <span className="text-gray-500">Document ID</span>
              <p className="font-mono text-xs">{result.document_id}</p>
            </div>
            <div>
              <span className="text-gray-500">Task ID</span>
              <p className="font-mono text-xs">{result.task_id || "—"}</p>
            </div>
          </div>
          <div className="flex gap-3 pt-2">
            <Link
              to={`/admin/documents/${result.document_id}`}
              className="rounded-pill bg-primary px-6 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              View Document
            </Link>
            <button
              onClick={() => {
                setFile(null);
                setResult(null);
              }}
              className="rounded-pill border border-gray-300 px-6 py-2 text-sm text-gray-600 hover:bg-gray-50"
            >
              Import Another
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
