import { useState } from "react";
import { getAccessToken } from "../services/auth";

const BASE_URL = import.meta.env.VITE_API_URL;

/**
 * Button that triggers a file download from the backend.
 *
 * Props:
 *   endpoint – backend path (e.g. "/risk/export")
 *   label    – button text (default: "Export")
 *   fileName – suggested download filename
 */
export default function ExportButton({
  endpoint,
  label = "Export",
  fileName = "export.xlsx",
}) {
  const [loading, setLoading] = useState(false);

  async function handleExport() {
    setLoading(true);
    try {
      const token = await getAccessToken();
      const res = await fetch(`${BASE_URL}${endpoint}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      if (!res.ok) throw new Error("Download failed");

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Export error:", err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <button
      className="export-btn"
      onClick={handleExport}
      disabled={loading}
    >
      {loading ? (
        <>
          <span className="spinner spinner--sm" /> Exporting…
        </>
      ) : (
        <>📥 {label}</>
      )}
    </button>
  );
}
