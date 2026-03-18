import { useState, KeyboardEvent } from "react";
import {
  Box,
  Paper,
  Stack,
  TextField,
  IconButton,
  CircularProgress,
  Typography,
} from "@mui/material";
import SendIcon from "@mui/icons-material/Send";

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

interface ICQaChatPanelProps {
  loading: boolean;
  /** 送出問題，回傳 API 的 answer 字串，失敗請 throw */
  onSend: (text: string) => Promise<string | void>;
  initialMessages?: ChatMessage[];
}

export function ICQaChatPanel({ loading, onSend, initialMessages }: ICQaChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages ?? []);
  const [input, setInput] = useState("");

  const handleSendInternal = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: ChatMessage = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");

    const appendAssistant = (content: string) => {
      const assistantMsg: ChatMessage = { role: "assistant", content };
      setMessages((prev) => [...prev, assistantMsg]);
    };

    try {
      const result = await onSend(text);
      if (result != null && result !== "") {
        appendAssistant(result);
      }
    } catch (e: any) {
      appendAssistant(`(發生錯誤) ${e?.message ?? String(e)}`);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void handleSendInternal();
    }
  };

  return (
    <Paper variant="outlined" sx={{ p: 2, height: "100%", display: "flex", flexDirection: "column" }}>
      <Typography variant="subtitle1" gutterBottom>
        IC / QA 查詢對話
      </Typography>
      <Box
        sx={{
          flex: 1,
          overflowY: "auto",
          mb: 1.5,
          pr: 1,
        }}
      >
        <Stack spacing={1}>
          {messages.map((m, idx) => (
            <Box
              key={idx}
              sx={{
                alignSelf: m.role === "user" ? "flex-end" : "flex-start",
                maxWidth: "80%",
              }}
            >
              <Paper
                sx={{
                  p: 1,
                  bgcolor: (theme) =>
                    m.role === "user"
                      ? theme.palette.primary.main
                      : theme.palette.grey[100],
                  color: m.role === "user" ? "primary.contrastText" : "text.primary",
                }}
              >
                <Typography variant="body2" whiteSpace="pre-wrap">
                  {m.content}
                </Typography>
              </Paper>
            </Box>
          ))}
          {loading && (
            <Box sx={{ display: "flex", justifyContent: "flex-start", pl: 1, pt: 0.5 }}>
              <CircularProgress size={18} />
            </Box>
          )}
        </Stack>
      </Box>
      <Box sx={{ display: "flex", gap: 1 }}>
        <TextField
          size="small"
          fullWidth
          placeholder="輸入問題，例如：IC卡 D12 錯誤 代表什麼？"
          multiline
          maxRows={3}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <IconButton
          color="primary"
          onClick={() => void handleSendInternal()}
          disabled={loading || !input.trim()}
        >
          <SendIcon />
        </IconButton>
      </Box>
    </Paper>
  );
}

export default ICQaChatPanel;

