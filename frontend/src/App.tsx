import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline, AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { styled } from '@mui/material/styles';
import darkTheme from './theme/darkTheme';
import Leaderboard from './pages/Leaderboard';
import Registration from './pages/Registration';

// Styled components
const StyledAppBar = styled(AppBar)(({ theme }) => ({
  background: 'linear-gradient(135deg, #ff4655 0%, #ff8a80 100%)',
  boxShadow: '0 4px 20px rgba(255, 70, 85, 0.3)',
}));

const StyledButton = styled(Button)(({ theme }) => ({
  color: '#fff',
  textTransform: 'none',
  fontWeight: 600,
  '&:hover': {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
  },
}));

function App() {
  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Router>
        <StyledAppBar position="static">
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 700 }}>
              ValorantSL
            </Typography>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Link to="/" style={{ textDecoration: 'none' }}>
                <StyledButton>
                  Leaderboard
                </StyledButton>
              </Link>
              <Link to="/register" style={{ textDecoration: 'none' }}>
                <StyledButton>
                  Register
                </StyledButton>
              </Link>
            </Box>
          </Toolbar>
        </StyledAppBar>
        
        <Routes>
          <Route path="/" element={<Leaderboard />} />
          <Route path="/register" element={<Registration />} />
          <Route path="/auth/callback" element={<Registration />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;
