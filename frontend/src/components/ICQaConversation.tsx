import { useState, KeyboardEvent } from "react";
import {
  Alert,
  Box,
  Button,
  Collapse,
  IconButton,
  Paper,
  Stack,
  TextField,
  Typography,
  CircularProgress,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import SendIcon from "@mui/icons-material/Send";
import type { GraphragQueryResponse, QaSearchResponse } from "../types/icQa";

export type ConversationTurn = {
  id: string;
  userText: string;
  response: GraphragQueryResponse | QaSearchResponse | null;
  error: string | null;
};

type Mode = "graphrag" | "qa";

interface ICQaConversationProps {
  turns: ConversationTurn[];
  loading: boolean;
  mode: Mode;
  onSend: (text: string) => Promise<string | void>;
}

function getAnswer(turn: ConversationTurn): string {
  if (turn.error) return "";
  const r = turn.response;
  if (!r) return "";
  const g = r as GraphragQueryResponse;
  if (g.answer !== undefined) {
    return g.answer ?? "";
  }
  const q = r as QaSearchResponse;
  if (q.answer != null) {
    return q.answer;
  }
  if (q.results && q.results.length > 0) {
    return "此模式僅提供 QA 列表結果，請展開下方「QA 結果」查看詳細內容。";
  }
  return "";
}

function SourcesOrResults({
  data: response,
  mode,
}: {
  data: GraphragQueryResponse | QaSearchResponse | null;
  mode: Mode;
}) {
  if (!response) {
    return (
      <Typography variant="body2" color="text.secondary">
        尚無查詢結果。
      </Typography>
    );
  }
  if (mode === "graphrag") {
    const d = response as GraphragQueryResponse;
    if (!d.sources?.length) {
      return (
        <Typography variant="body2" color="text.secondary">
          無來源資料。
        </Typography>
      );
    }
    return (
      <Stack spacing={1} sx={{ mt: 1 }}>
        {d.sources.map((s, idx) => (
          <Paper key={s.id || idx} variant="outlined" sx={{ p: 1.5 }}>
            <Typography variant="caption" color="text.secondary">
              {s.id} {s.score !== undefined ? `(score: ${s.score.toFixed(3)})` : ""}
            </Typography>
            <Typography variant="body2" whiteSpace="pre-wrap" sx={{ mt: 0.5 }}>
              {s.content}
            </Typography>
          </Paper>
        ))}
      </Stack>
    );
  }
  const d = response as QaSearchResponse;
  if (!d.results?.length) {
    return (
      <Typography variant="body2" color="text.secondary">
        無 QA 結果。
      </Typography>
    );
  }
  return (
    <Stack spacing={1} sx={{ mt: 1 }}>
      {d.results.map((r) => (
        <Paper key={r.id} variant="outlined" sx={{ p: 1.5 }}>
          <Typography variant="caption" color="text.secondary">
            {r.id} {r.qa_number ? `#${r.qa_number}` : ""}
          </Typography>
          <Typography variant="subtitle2" sx={{ mt: 0.5 }}>
            Q: {r.question}
          </Typography>
          <Typography variant="body2" whiteSpace="pre-wrap" sx={{ mt: 0.5 }}>
            A: {r.answer}
          </Typography>
          {r.keywords?.length ? (
            <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: "block" }}>
              keywords: {r.keywords.join(", ")}
            </Typography>
          ) : null}
        </Paper>
      ))}
    </Stack>
  );
}

export function ICQaConversation({ turns, loading, mode, onSend }: ICQaConversationProps) {
  const [input, setInput] = useState("");
  const [sourcesOpen, setSourcesOpen] = useState<Record<string, boolean>>({});
  const [rawOpen, setRawOpen] = useState<Record<string, boolean>>({});

  const toggleSources = (id: string) => {
    setSourcesOpen((prev) => ({ ...prev, [id]: !prev[id] }));
  };
  const toggleRaw = (id: string) => {
    setRawOpen((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    try {
      await onSend(text);
    } catch (_) {
      // Error is shown per-turn in the assistant card
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void handleSend();
    }
  };

  return (
    <Paper
      variant="outlined"
      sx={{
        p: 2,
        height: "100%",
        minHeight: 400,
        display: "flex",
        flexDirection: "column",
        borderRadius: 2,
      }}
    >
      <Box sx={{ flex: 1, overflowY: "auto", mb: 2, pr: 0.5 }}>
        <Stack spacing={2}>
          {turns.length === 0 && !loading && (
            <Box
              sx={{
                mt: 4,
                px: 2,
                py: 3,
                maxWidth: 520,
                mx: "auto",
                borderRadius: 2,
                border: 1,
                borderColor: "divider",
                bgcolor: (t) => t.palette.background.default,
              }}
            >
              <Typography variant="subtitle1" gutterBottom>
                開始提問
              </Typography>
              <Typography variant="body2" color="text.secondary">
                請輸入門診、批價或病歷相關問題，例如：
                <br />
                「IC 卡 D12 錯誤代表什麼？」或「未帶卡如何建檔？」
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 1.5 }}>
                Enter 送出，Shift+Enter 換行。
              </Typography>
            </Box>
          )}
          {turns.map((turn) => (
            <Stack key={turn.id} spacing={1}>
              <Box sx={{ alignSelf: "flex-end", maxWidth: "85%" }}>
                <Paper
                  sx={{
                    p: 1.5,
                    bgcolor: "primary.main",
                    color: "primary.contrastText",
                    borderRadius: 2,
                  }}
                >
                  <Typography variant="body2" whiteSpace="pre-wrap">
                    {turn.userText}
                  </Typography>
                </Paper>
              </Box>
              <Box sx={{ alignSelf: "flex-start", maxWidth: "95%" }}>
                <Paper
                  variant="outlined"
                  sx={{
                    p: 2,
                    borderRadius: 2,
                    bgcolor: (t) => t.palette.grey[50],
                    borderColor: (t) => t.palette.grey[200],
                  }}
                >
                  {turn.error ? (
                    <Alert severity="error" sx={{ mb: 1 }}>
                      {turn.error}
                    </Alert>
                  ) : null}
                  <Typography variant="body1" sx={{ fontWeight: 500, mb: 1 }} component="div">
                    {getAnswer(turn)}
                  </Typography>
                  <Stack direction="row" flexWrap="wrap" gap={1} sx={{ mt: 1 }}>
                    <Button
                      size="small"
                      variant="outlined"
                      onClick={() => toggleSources(turn.id)}
                      aria-expanded={sourcesOpen[turn.id] ?? false}
                      endIcon={sourcesOpen[turn.id] ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                    >
                      {mode === "graphrag"
                        ? sourcesOpen[turn.id]
                          ? "隱藏來源"
                          : "查看來源"
                        : sourcesOpen[turn.id]
                          ? "隱藏 QA 結果"
                          : "查看 QA 結果"}
                    </Button>
                    <Button
                      size="small"
                      variant="outlined"
                      onClick={() => toggleRaw(turn.id)}
                      aria-expanded={rawOpen[turn.id] ?? false}
                      endIcon={rawOpen[turn.id] ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                    >
                      {rawOpen[turn.id] ? "隱藏 Raw JSON" : "查看 Raw JSON"}
                    </Button>
                  </Stack>
                  <Collapse in={sourcesOpen[turn.id] ?? false}>
                    <Box sx={{ mt: 1.5, pt: 1.5, borderTop: 1, borderColor: "divider" }}>
                      <Typography variant="caption" color="text.secondary" gutterBottom component="div">
                        {mode === "graphrag" ? "Sources" : "QA Results"}
                      </Typography>
                      <SourcesOrResults data={turn.response} mode={mode} />
                    </Box>
                  </Collapse>
                  <Collapse in={rawOpen[turn.id] ?? false}>
                    <Box sx={{ mt: 1.5, pt: 1.5, borderTop: 1, borderColor: "divider" }}>
                      <Typography variant="caption" color="text.secondary" gutterBottom component="div">
                        Raw JSON
                      </Typography>
                      <Box
                        component="pre"
                        sx={{
                          mt: 0.5,
                          p: 1.5,
                          borderRadius: 1,
                          bgcolor: "grey.900",
                          color: "grey.100",
                          fontSize: 12,
                          maxHeight: 280,
                          overflow: "auto",
                        }}
                      >
                        {turn.response ? JSON.stringify(turn.response, null, 2) : "// 尚無資料"}
                      </Box>
                    </Box>
                  </Collapse>
                </Paper>
              </Box>
            </Stack>
          ))}
          {loading && (
            <Box sx={{ display: "flex", alignItems: "center", gap: 1, pl: 0.5 }}>
              <CircularProgress size={20} />
              <Typography variant="body2" color="text.secondary">
                查詢中…
              </Typography>
            </Box>
          )}
        </Stack>
      </Box>
      <Box sx={{ display: "flex", gap: 1, alignItems: "flex-end" }}>
        <TextField
          size="small"
          fullWidth
          placeholder="輸入問題，例如：IC卡 D12 錯誤 代表什麼？"
          multiline
          maxRows={3}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          sx={{ "& .MuiOutlinedInput-root": { borderRadius: 2 } }}
        />
        <IconButton
          color="primary"
          onClick={() => void handleSend()}
          disabled={loading || !input.trim()}
          sx={{ mb: 0.5 }}
          aria-label="送出"
        >
          <SendIcon />
        </IconButton>
      </Box>
    </Paper>
  );
}

export default ICQaConversation;
