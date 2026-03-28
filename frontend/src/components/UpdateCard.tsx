import type { AwsUpdate } from "../types/update";

interface Props {
  update: AwsUpdate;
  onClick: (update: AwsUpdate) => void;
}

export function UpdateCard({ update, onClick }: Props) {
  const categories = update.category
    ? update.category.split(",").map((c) => c.trim()).filter(Boolean)
    : [];

  const useCases = update.use_cases_ja
    ? update.use_cases_ja
        .split("\n")
        .map((line) => line.replace(/^[-・]\s*/, "").trim())
        .filter(Boolean)
    : [];

  return (
    <article
      className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 hover:shadow-md hover:border-orange-300 transition-all cursor-pointer"
      onClick={() => onClick(update)}
    >
      <div className="flex items-start justify-between gap-3 mb-2">
        <time className="text-xs text-gray-400 shrink-0 mt-0.5">
          {update.published_date}
        </time>
        {categories.length > 0 && (
          <div className="flex flex-wrap gap-1 justify-end">
            {categories.slice(0, 2).map((cat) => (
              <span
                key={cat}
                className="text-xs bg-orange-50 text-orange-700 border border-orange-200 px-2 py-0.5 rounded-full"
              >
                category:{cat.split("/").pop()}
              </span>
            ))}
          </div>
        )}
      </div>
      <h2 className="text-sm font-bold text-gray-800 mb-2 leading-snug line-clamp-2">
        {update.title_ja || update.title}
      </h2>
      {update.page_summary_ja && (
        <p className="text-xs text-gray-600 line-clamp-3 leading-relaxed mb-2">
          {update.page_summary_ja}
        </p>
      )}
      {useCases.length > 0 && (
        <ul className="space-y-0.5 mb-2">
          {useCases.slice(0, 3).map((uc, i) => (
            <li key={i} className="flex gap-1.5 text-xs text-gray-600">
              <span className="text-orange-400 shrink-0">•</span>
              <span className="line-clamp-1">{uc}</span>
            </li>
          ))}
        </ul>
      )}
      <div className="mt-2 text-xs text-orange-500 font-medium">詳細を見る</div>
    </article>
  );
}
