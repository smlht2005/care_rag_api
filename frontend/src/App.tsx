import { Container, AppBar, Toolbar, Typography, Box } from "@mui/material";
import ICQaConsolePage from "./pages/ICQaConsolePage";

function App() {
  return (
    <Box sx={{ minHeight: "100vh", bgcolor: (t) => t.palette.background.default }}>
      <AppBar position="static" color="primary" enableColorOnDark>
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            his 諮服QA
          </Typography>
        </Toolbar>
      </AppBar>
      <Container maxWidth="lg" sx={{ py: 3 }}>
        <ICQaConsolePage />
      </Container>
    </Box>
  );
}

export default App;

