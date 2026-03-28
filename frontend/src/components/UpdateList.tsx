import type { AwsUpdate } from "../types/update";
import { UpdateCard } from "./UpdateCard";

interface Props {
  items: AwsUpdate[];
  total: number;
  page: number;
  limit: number;
  loading: boolean;
  onPageChange: (page: number) => void;
  onSelect: (update: AwsUpdate) => void;
}

export function UpdateList({
  items,
  total,
  page,
  limit,
  loading,
  onPageChange,
  onSelect,
}: Props) {
  const totalPages = Math.ceil(total / limit);

  if (loading) {
    return (
      <div className="flex justify-center py-20 text-gray-400 text-sm">
        読み込み中...
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="flex justify-center py-20 text-gray-400 text-sm">
        該当するアップデートが見つかりませんでした
      </div>
    );
  }

  return (
    <div>
      <p className="text-xs text-gray-400 mb-4">
        {total} 件中 {(page - 1) * limit + 1}〜{Math.min(page * limit, total)} 件を表示
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        {items.map((item) => (
          <UpdateCard key={item.id} update={item} onClick={onSelect} />
        ))}
      </div>

      {/* ページネーション */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2 flex-wrap">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            className="px-3 py-1.5 rounded-lg text-sm border border-gray-300 disabled:opacity-30 hover:bg-gray-100 transition-colors"
          >
            ← 前へ
          </button>
          {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
            const p = i + 1;
            return (
              <button
                key={p}
                onClick={() => onPageChange(p)}
                className={`px-3 py-1.5 rounded-lg text-sm border transition-colors ${
                  p === page
                    ? "bg-orange-500 text-white border-orange-500"
                    : "border-gray-300 hover:bg-gray-100"
                }`}
              >
                {p}
              </button>
            );
          })}
          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
            className="px-3 py-1.5 rounded-lg text-sm border border-gray-300 disabled:opacity-30 hover:bg-gray-100 transition-colors"
          >
            次へ →
          </button>
        </div>
      )}
    </div>
  );
}
