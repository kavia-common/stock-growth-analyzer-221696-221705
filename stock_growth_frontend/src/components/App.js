import React, { useState } from "react";
import SearchForm from "./SearchForm";
import { analyzeGrowth } from "./ApiClient";

/**
 * PUBLIC_INTERFACE
 * App: container component that submits search payloads to backend, displays errors, warnings, and results.
 */
function App() {
  const [rows, setRows] = useState([]);
  const [warnings, setWarnings] = useState([]);
  const [error, setError] = useState("");

  const onSubmit = async (payload) => {
    setError("");
    setWarnings([]);
    setRows([]);
    try {
      const { results, warnings } = await analyzeGrowth(payload);
      setRows(results || []);
      setWarnings(warnings || []);
      if ((results || []).length === 0 && (!warnings || warnings.length === 0)) {
        setWarnings([
          "No results were returned. Likely the selected dates are non-trading days (weekend/holiday) "
          + "or the data provider lacks coverage for chosen symbols. Try shifting to nearby business days "
          + "or adjust the universe/tickers."
        ]);
      }
    } catch (e) {
      setError(e.message || "Failed to fetch results.");
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-4 md:p-6">
      <div className="max-w-6xl mx-auto space-y-4">
        <h1 className="text-2xl font-semibold">Stock Growth Analyzer</h1>
        <SearchForm onSubmit={onSubmit} />

        {error && (
          <div className="p-3 rounded border border-red-300 bg-red-50 text-red-700">
            Error: {error}
          </div>
        )}

        {warnings && warnings.length > 0 && (
          <div className="p-3 rounded border border-yellow-300 bg-yellow-50 text-yellow-800">
            <div className="font-medium mb-1">Warnings</div>
            <ul className="list-disc list-inside text-sm">
              {warnings.map((w, idx) => (
                <li key={idx}>{w}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="bg-white rounded shadow overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 py-2 text-left">Ticker</th>
                <th className="px-3 py-2 text-left">Start</th>
                <th className="px-3 py-2 text-left">End</th>
                <th className="px-3 py-2 text-right">Start Price</th>
                <th className="px-3 py-2 text-right">End Price</th>
                <th className="px-3 py-2 text-right">Growth %</th>
                <th className="px-3 py-2 text-right">Abs Return</th>
                <th className="px-3 py-2 text-right">Data Points</th>
                <th className="px-3 py-2 text-left">Warning</th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 ? (
                <tr>
                  <td className="px-3 py-3 text-gray-500" colSpan={9}>
                    No data to display yet.
                  </td>
                </tr>
              ) : (
                rows.map((r, idx) => (
                  <tr key={idx} className="border-t">
                    <td className="px-3 py-2">{r.ticker}</td>
                    <td className="px-3 py-2">{r.start_date_effective || "-"}</td>
                    <td className="px-3 py-2">{r.end_date_effective || "-"}</td>
                    <td className="px-3 py-2 text-right">
                      {r.start_price !== null && r.start_price !== undefined ? r.start_price.toFixed(2) : "-"}
                    </td>
                    <td className="px-3 py-2 text-right">
                      {r.end_price !== null && r.end_price !== undefined ? r.end_price.toFixed(2) : "-"}
                    </td>
                    <td className="px-3 py-2 text-right">
                      {r.growth_pct !== null && r.growth_pct !== undefined ? r.growth_pct.toFixed(2) : "-"}
                    </td>
                    <td className="px-3 py-2 text-right">
                      {r.absolute_return !== null && r.absolute_return !== undefined ? r.absolute_return.toFixed(2) : "-"}
                    </td>
                    <td className="px-3 py-2 text-right">
                      {r.data_points !== null && r.data_points !== undefined ? r.data_points : "-"}
                    </td>
                    <td className="px-3 py-2">{r.warning || ""}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default App;
