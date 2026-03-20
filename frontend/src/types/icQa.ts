export interface GraphragSource {
  id: string;
  content: string;
  score?: number;
  metadata?: Record<string, any>;
}

export interface GraphragQueryResponse {
  answer: string | null;
  sources: GraphragSource[];
  query: string;
  provider?: string | null;
}

export interface QaSearchResult {
  id: string;
  qa_number?: string;
  question: string;
  answer: string;
  scenario?: string;
  keywords?: string[];
  steps?: string[];
  notes?: string;
  metadata?: Record<string, any>;
}

export interface QaSearchResponse {
  query: string;
  total: number;
  results: QaSearchResult[];
  answer: string | null;
}

