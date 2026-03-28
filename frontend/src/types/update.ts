export interface AwsUpdate {
  id: string;
  published_date: string; // "YYYY-MM-DD"
  title: string;
  title_ja: string | null;
  summary_en: string | null;
  source_url: string;
  page_summary_ja: string | null;
  use_cases_ja: string | null;
  category: string | null;
  collected_at: string;
}

export interface ListResponse {
  items: AwsUpdate[];
  total: number;
  page: number;
  limit: number;
}

export interface FilterParams {
  page: number;
  limit: number;
  date_from?: string;
  date_to?: string;
  category?: string;
  q?: string;
}
