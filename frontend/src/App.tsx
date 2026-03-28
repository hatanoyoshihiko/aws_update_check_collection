import { useCallback, useEffect, useState } from "react";
import { fetchUpdates } from "./api/updates";
import { FilterBar } from "./components/FilterBar";
import { UpdateDetail } from "./components/UpdateDetail";
import { UpdateList } from "./components/UpdateList";
import type { AwsUpdate, FilterParams } from "./types/update";

const DEFAULT_LIMIT = 20;

export default function App() {
  const [items, setItems] = useState<AwsUpdate[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<AwsUpdate | null>(null);
  const [filters, setFilters] = useState<Omit<FilterParams, "page" | "limit">>({});

  const load = useCallback(
    async (currentPage: number, currentFilters: Omit<FilterParams, "page" | "limit">) => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetchUpdates({
          page: currentPage,
          limit: DEFAULT_LIMIT,
          ...currentFilters,
        });
        setItems(res.items);
        setTotal(res.total);
      } catch (e) {
        setError(e instanceof Error ? e.message : "データの取得に失敗しました");
      } finally {
        setLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    void load(page, filters);
  }, [load, page, filters]);

  function handleFilter(newFilters: Omit<FilterParams, "page" | "limit">) {
    setFilters(newFilters);
    setPage(1);
  }

  function handlePageChange(newPage: number) {
    setPage(newPage);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* ヘッダー */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center gap-3">
          <span className="text-2xl">☁️</span>
          <div>
            <h1 className="text-lg font-bold text-gray-900 leading-tight">
              AWS Update Collection
            </h1>
            <p className="text-xs text-gray-500">
              AWS 新機能・アップデート情報を日本語で確認
            </p>
          </div>
        </div>
      </header>

      {/* メインコンテンツ */}
      <main className="max-w-6xl mx-auto px-4 py-6">
        <FilterBar onFilter={handleFilter} />

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-3 mb-6 text-sm">
            エラー: {error}
          </div>
        )}

        <UpdateList
          items={items}
          total={total}
          page={page}
          limit={DEFAULT_LIMIT}
          loading={loading}
          onPageChange={handlePageChange}
          onSelect={setSelected}
        />
      </main>

      {/* 詳細モーダル */}
      {selected && (
        <UpdateDetail update={selected} onClose={() => setSelected(null)} />
      )}
    </div>
  );
}
