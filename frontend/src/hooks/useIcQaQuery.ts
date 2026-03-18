import { useCallback, useState } from "react";
import type { GraphragQueryResponse, QaSearchResponse } from "../types/icQa";

type Mode = "graphrag" | "qa";

interface UseIcQaQueryOptions {
  mode: Mode;
}

export interface RunQueryResult {
  answer: string;
  response: GraphragQueryResponse | QaSearchResponse | null;
  error: string | null;
}

interface UseIcQaQueryResult {
  data: GraphragQueryResponse | QaSearchResponse | null;
  loading: boolean;
  error: string | null;
  /** 執行查詢，回傳 { answer, response, error }，不 throw */
  runQuery: (query: string, topK: number) => Promise<RunQueryResult>;
}

const API_BASE = "/api/v1";

export function useIcQaQuery(options: UseIcQaQueryOptions): UseIcQaQueryResult {
  const { mode } = options;

  const [data, setData] = useState<GraphragQueryResponse | QaSearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runQuery = useCallback(
    async (query: string, topK: number) => {
      if (!query.trim()) {
        return { answer: "", response: null, error: null };
      }
      setLoading(true);
      setError(null);

      try {
        let url: string;
        let body: unknown;

        if (mode === "graphrag") {
          url = `${API_BASE}/query`;
          body = {
            query,
            top_k: topK,
            skip_cache: true,
          };
        } else {
          url = `${API_BASE}/qa/search`;
          body = {
            query,
            limit: topK,
          };
        }

        const res = await fetch(url, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            // 若後端啟用 X-API-Key，可在此注入或改為從環境變數 / 設定讀取
            "X-API-Key": "test-api-key",
          },
          body: JSON.stringify(body),
        });

        if (!res.ok) {
          const text = await res.text();
          const errMsg = `HTTP ${res.status}: ${text}`;
          setError(errMsg);
          setData(null);
          setLoading(false);
          return { answer: "", response: null, error: errMsg };
        }

        const json = (await res.json()) as GraphragQueryResponse | QaSearchResponse;
        setData(json);
        const answer =
          (json as GraphragQueryResponse).answer ??
          (json as QaSearchResponse).answer ??
          "";
        setLoading(false);
        return { answer, response: json, error: null };
      } catch (e: any) {
        const errMsg = e?.message ?? String(e);
        setError(errMsg);
        setData(null);
        setLoading(false);
        return { answer: "", response: null, error: errMsg };
      }
    },
    [mode],
  );

  return { data, loading, error, runQuery };
}

