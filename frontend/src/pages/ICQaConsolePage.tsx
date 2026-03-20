import { Box, Stack, TextField, Typography, Button } from "@mui/material";
import DeleteSweepIcon from "@mui/icons-material/DeleteSweep";
import { useState } from "react";
import { useIcQaQuery } from "../hooks/useIcQaQuery";
import ICQaConversation, { type ConversationTurn } from "../components/ICQaConversation";
import { createId } from "../utils/id";

function ICQaConsolePage() {
  const [topK, setTopK] = useState(5);
  const [turns, setTurns] = useState<ConversationTurn[]>([]);

  // 前端僅使用 GraphRAG 問答（/api/v1/query）
  const { loading, runQuery } = useIcQaQuery({ mode: "graphrag" });

  const handleSend = async (text: string): Promise<string | void> => {
    const result = await runQuery(text, topK);
    setTurns((prev) => [
      ...prev,
      {
        id: createId(),
        userText: text,
        response: result.response,
        error: result.error,
      },
    ]);
    return result.answer;
  };

  const handleClear = () => setTurns([]);

  return (
    <Stack spacing={2} sx={{ height: "100%", minHeight: 0 }}>
      <Box
        sx={{
          display: "flex",
          flexDirection: { xs: "column", sm: "row" },
          alignItems: { xs: "flex-start", sm: "center" },
          gap: 2,
          py: 1,
          px: 0.5,
        }}
      >
        <Typography variant="subtitle2" color="text.secondary" sx={{ mr: 0.5 }}>
          查詢設定
        </Typography>
        <Typography variant="body2" color="text.secondary">
          模式：GraphRAG 問答（/api/v1/query）
        </Typography>
        <TextField
          size="small"
          type="number"
          label="Top K / Limit"
          value={topK}
          onChange={(e) => setTopK(Math.max(1, Number(e.target.value) || 1))}
          sx={{ width: 120 }}
          inputProps={{ min: 1 }}
          helperText="每次回傳的來源筆數，建議 3–10。"
        />
        <Button
          size="small"
          variant="outlined"
          startIcon={<DeleteSweepIcon />}
          onClick={handleClear}
          disabled={turns.length === 0}
        >
          清除對話
        </Button>
      </Box>
      <Box sx={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
        <ICQaConversation turns={turns} loading={loading} mode="graphrag" onSend={handleSend} />
      </Box>
    </Stack>
  );
}

export default ICQaConsolePage;
