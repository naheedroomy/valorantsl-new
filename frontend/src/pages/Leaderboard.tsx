import React from 'react';
import {
  Container,
  Typography,
  Box,
  AppBar,
  Toolbar,
  Paper,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import LeaderboardTable from '../components/LeaderboardTable';

const StyledAppBar = styled(AppBar)(({ theme }) => ({
  marginBottom: theme.spacing(3),
  background: `linear-gradient(135deg, ${theme.palette.primary.main}20 0%, ${theme.palette.background.paper} 100%)`,
  backdropFilter: 'blur(10px)',
}));

const StatsCard = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(2),
  textAlign: 'center',
  background: `linear-gradient(135deg, ${theme.palette.background.paper} 0%, ${theme.palette.background.default} 100%)`,
  border: `1px solid ${theme.palette.divider}`,
  borderRadius: theme.spacing(1),
}));

const ValorantTitle = styled(Typography)(({ theme }) => ({
  background: `linear-gradient(45deg, ${theme.palette.primary.main}, #ff6b6b)`,
  WebkitBackgroundClip: 'text',
  WebkitTextFillColor: 'transparent',
  backgroundClip: 'text',
  fontWeight: 700,
  textShadow: `0 0 20px ${theme.palette.primary.main}40`,
}));

const Leaderboard: React.FC = () => {
  return (
    <Box sx={{ flexGrow: 1 }}>
      <Container maxWidth="xl" sx={{ pt: 4, pb: 4 }}>
        {/* Main Leaderboard Table */}
        <Box sx={{ px: { xs: 1, sm: 2, md: 4, lg: 6, xl: 8 } }}>
          <Paper sx={{ p: 0, borderRadius: 2 }} elevation={3}>
            <Box sx={{ p: 3, pb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Typography variant="h2" sx={{ fontSize: '2.5rem' }}>
                  🇱🇰
                </Typography>
                <Box>
                  <Typography variant="h5" gutterBottom color="text.primary">
                    Sri Lanka Valorant Leaderboard
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Showing 50 players per page • Updated in real-time
                  </Typography>
                </Box>
              </Box>
              <Box sx={{ display: 'flex', gap: 1 }}>
                {/* Navigation buttons will go here when needed */}
              </Box>
            </Box>
            <LeaderboardTable perPage={50} />
          </Paper>
        </Box>
      </Container>
    </Box>
  );
};

export default Leaderboard;