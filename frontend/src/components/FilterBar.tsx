import { type ChangeEvent, type FormEvent, useEffect, useState } from "react";
import { fetchCategories } from "../api/updates";
import type { FilterParams } from "../types/update";

interface Props {
  onFilter: (params: Omit<FilterParams, "page" | "limit">) => void;
}

export function FilterBar({ onFilter }: Props) {
  const [q, setQ] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [category, setCategory] = useState("");
  const [categories, setCategories] = useState<string[]>([]);

  const categoryOptions = categories.reduce<Array<{ label: string; value: string }>>(
    (acc, cat) => {
      const label = cat.split("/").pop()!.split(":").pop()!;
      if (!acc.some((o) => o.label === label)) {
        acc.push({ label, value: label });
      }
      return acc;
    },
    []
  );

  useEffect(() => {
    fetchCategories()
      .then(setCategories)
      .catch(() => {/* フォールバック: 空リストのまま */});
  }, []);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    onFilter({
      q: q || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
      category: category || undefined,
    });
  }

  function handleReset() {
    setQ("");
    setDateFrom("");
    setDateTo("");
    setCategory("");
    onFilter({});
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 mb-6 flex flex-col gap-3"
    >
      <div className="flex flex-col gap-1">
        <label className="text-xs font-medium text-gray-500">キーワード</label>
        <input
          type="text"
          value={q}
          onChange={(e: ChangeEvent<HTMLInputElement>) => setQ(e.target.value)}
          placeholder="例: S3, Lambda..."
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400"
        />
      </div>
      <div className="flex flex-col gap-1">
        <label className="text-xs font-medium text-gray-500">カテゴリ</label>
        <select
          value={category}
          onChange={(e: ChangeEvent<HTMLSelectElement>) => setCategory(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400 bg-white"
        >
          <option value="">すべて</option>
          {categoryOptions.map(({ label, value }) => (
            <option key={value} value={value}>category:{label}</option>
          ))}
        </select>
      </div>
      <div className="flex gap-3">
        <div className="flex flex-col gap-1 flex-1">
          <label className="text-xs font-medium text-gray-500">開始日</label>
          <input
            type="date"
            value={dateFrom}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setDateFrom(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400"
          />
        </div>
        <div className="flex flex-col gap-1 flex-1">
          <label className="text-xs font-medium text-gray-500">終了日</label>
          <input
            type="date"
            value={dateTo}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setDateTo(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400"
          />
        </div>
      </div>
      <div className="flex gap-2">
        <button
          type="submit"
          className="bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          検索
        </button>
        <button
          type="button"
          onClick={handleReset}
          className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          リセット
        </button>
      </div>
    </form>
  );
}
