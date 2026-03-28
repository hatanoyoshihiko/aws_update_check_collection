import type { AwsUpdate } from "../types/update";

interface Props {
  update: AwsUpdate;
  onClose: () => void;
}

export function UpdateDetail({ update, onClose }: Props) {
  const useCases = update.use_cases_ja
    ? update.use_cases_ja
        .split("\n")
        .map((line) => line.replace(/^[-・]\s*/, "").trim())
        .filter(Boolean)
    : [];

  return (
    <div
      className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* ヘッダー */}
        <div className="sticky top-0 bg-white border-b border-gray-100 px-6 py-4 flex items-start justify-between gap-4 rounded-t-2xl">
          <div className="flex-1">
            <time className="text-xs text-gray-400 block mb-1">
              {update.published_date}
            </time>
            <h2 className="text-base font-bold text-gray-900 leading-snug">
              {update.title_ja || update.title}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl shrink-0 mt-0.5"
            aria-label="閉じる"
          >
            ✕
          </button>
        </div>

        {/* 本文 */}
        <div className="px-6 py-5 space-y-5">
          {/* 日本語要約 */}
          {update.page_summary_ja && (
            <section>
              <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2">
                ページ要約
              </h3>
              <p className="text-sm text-gray-700 leading-relaxed bg-gray-50 rounded-lg p-3">
                {update.page_summary_ja}
              </p>
            </section>
          )}

          {/* 活用例 */}
          {useCases.length > 0 && (
            <section>
              <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2">
                活用例
              </h3>
              <ul className="space-y-2">
                {useCases.map((useCase, i) => (
                  <li key={i} className="flex gap-2 text-sm text-gray-700">
                    <span className="text-orange-400 shrink-0">•</span>
                    <span>{useCase}</span>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {/* 参照元URL */}
          <section>
            <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2">
              参照元URL
            </h3>
            <a
              href={update.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-orange-500 hover:text-orange-700 underline break-all"
            >
              {update.source_url}
            </a>
          </section>

          {/* 概要（英語原文） */}
          {update.summary_en && (
            <section>
              <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2">
                英語原文
              </h3>
              <p className="text-sm text-gray-500 leading-relaxed">
                {update.summary_en}
              </p>
            </section>
          )}
        </div>
      </div>
    </div>
  );
}
