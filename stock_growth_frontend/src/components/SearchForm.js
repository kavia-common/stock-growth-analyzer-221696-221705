import React, { useState } from "react";

/**
 * SearchForm component for entering tickers, date range, growth filters, limit and universe.
 * - When no tickers are provided, 'universe' is sent with the payload (default: NASDAQ).
 */
const SearchForm = ({ onSubmit }) => {
  const [tickers, setTickers] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [minGrowthPct, setMinGrowthPct] = useState("");
  const [maxGrowthPct, setMaxGrowthPct] = useState("");
  const [limit, setLimit] = useState(10);
  const [priceField, setPriceField] = useState("close");
  const [universe, setUniverse] = useState("NASDAQ"); // default NASDAQ

  const handleSubmit = (e) => {
    e.preventDefault();
    const parsedTickers = (tickers || "")
      .split(",")
      .map((t) => t.trim())
      .filter((t) => t.length > 0);

    const payload = {
      start_date: startDate,
      end_date: endDate,
      limit: Number(limit) || 10,
      price_field: priceField || "close",
    };

    if (minGrowthPct !== "") payload.min_growth_pct = Number(minGrowthPct);
    if (maxGrowthPct !== "") payload.max_growth_pct = Number(maxGrowthPct);

    if (parsedTickers.length > 0) {
      payload.tickers = parsedTickers;
    } else {
      // Include universe only when no tickers provided
      payload.universe = universe || "NASDAQ";
    }

    onSubmit && onSubmit(payload);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 bg-white p-4 rounded shadow">
      <div>
        <label className="block text-sm font-medium mb-1">Tickers (comma separated)</label>
        <input
          type="text"
          value={tickers}
          onChange={(e) => setTickers(e.target.value)}
          placeholder="e.g., AAPL, MSFT"
          className="w-full border rounded px-3 py-2"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">Start Date</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="w-full border rounded px-3 py-2"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">End Date</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="w-full border rounded px-3 py-2"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Limit</label>
          <input
            type="number"
            min="1"
            value={limit}
            onChange={(e) => setLimit(e.target.value)}
            className="w-full border rounded px-3 py-2"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">Min Growth %</label>
          <input
            type="number"
            value={minGrowthPct}
            onChange={(e) => setMinGrowthPct(e.target.value)}
            placeholder="e.g., 5"
            className="w-full border rounded px-3 py-2"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Max Growth %</label>
          <input
            type="number"
            value={maxGrowthPct}
            onChange={(e) => setMaxGrowthPct(e.target.value)}
            placeholder="e.g., 50"
            className="w-full border rounded px-3 py-2"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Price Field</label>
          <select
            value={priceField}
            onChange={(e) => setPriceField(e.target.value)}
            className="w-full border rounded px-3 py-2"
          >
            <option value="close">Close</option>
            <option value="adj_close">Adj Close</option>
            <option value="open">Open</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">Universe</label>
          <select
            value={universe}
            onChange={(e) => setUniverse(e.target.value)}
            className="w-full border rounded px-3 py-2"
          >
            <option value="NASDAQ">NASDAQ 100</option>
            <option value="SP500">S&P 500</option>
          </select>
          <p className="text-xs text-gray-500 mt-1">
            Only used when no tickers are provided.
          </p>
        </div>
      </div>

      <div>
        <button
          type="submit"
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
        >
          Analyze
        </button>
      </div>
    </form>
  );
};

export default SearchForm;
