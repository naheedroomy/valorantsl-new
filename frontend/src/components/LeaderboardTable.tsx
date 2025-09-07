import React, { useState, useEffect, useCallback } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Pagination,
  Box,
  Typography,
  Chip,
  Alert,
  Skeleton,
  IconButton,
  Tooltip,
  Collapse,
} from '@mui/material';
import { OpenInNew, EmojiEvents, KeyboardArrowDown, KeyboardArrowUp } from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import { LeaderboardEntry, LeaderboardResponse, PeakRank } from '../types/leaderboard';
import { leaderboardApi } from '../services/api';
import { getRankColor } from '../theme/darkTheme';

const StyledTableContainer = styled(TableContainer)(({ theme }) => ({
  borderRadius: theme.spacing(1),
  boxShadow: `0 4px 20px ${theme.palette.primary.main}20`,
  border: `1px solid ${theme.palette.divider}`,
}));

const RankChip = styled(Chip)<{ rank: string }>(({ theme, rank }) => ({
  backgroundColor: getRankColor(rank),
  color: theme.palette.getContrastText(getRankColor(rank)),
  fontWeight: 600,
  minWidth: '120px',
  boxShadow: `0 2px 8px ${getRankColor(rank)}40`,
}));

const EloCell = styled(TableCell)(({ theme }) => ({
  fontWeight: 600,
  fontSize: '1.1rem',
  color: theme.palette.primary.main,
}));

const RankCell = styled(TableCell)(() => ({
  fontWeight: 600,
  fontSize: '1.5rem',
  color: '#ff4655',
  textAlign: 'center',
  minWidth: '60px',
}));

interface LeaderboardTableProps {
  perPage?: number;
}

const formatLastPlayed = (dateString: string | null | undefined): string => {
  if (!dateString) return 'N/A';
  
  try {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    
    // Convert to different time units
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    // Format based on time difference
    if (diffMinutes < 1) return 'Just now';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    // For older dates, show the actual date
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
    });
  } catch (error) {
    return 'N/A';
  }
};

const LeaderboardTable: React.FC<LeaderboardTableProps> = ({ perPage = 50 }) => {
  const [data, setData] = useState<LeaderboardResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  const fetchLeaderboard = useCallback(async (page: number) => {
    try {
      setLoading(true);
      setError(null);
      const response = await leaderboardApi.getLeaderboard(page, perPage);
      setData(response);
    } catch (err) {
      console.error('Error fetching leaderboard:', err);
      setError('Failed to load leaderboard data. Please try again later.');
    } finally {
      setLoading(false);
    }
  }, [perPage]);

  useEffect(() => {
    fetchLeaderboard(currentPage);
  }, [currentPage, fetchLeaderboard]);

  const handlePageChange = (event: React.ChangeEvent<unknown>, page: number) => {
    setCurrentPage(page);
    setExpandedRows(new Set()); // Clear expanded rows when changing pages
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const calculateGlobalRank = (page: number, index: number): number => {
    return (page - 1) * perPage + index + 1;
  };

  const getRankIcon = (rank: number) => {
    if (rank === 1) return <EmojiEvents sx={{ color: '#FFD700', fontSize: '1.2rem' }} />; // Gold
    if (rank === 2) return <EmojiEvents sx={{ color: '#C0C0C0', fontSize: '1.2rem' }} />; // Silver  
    if (rank === 3) return <EmojiEvents sx={{ color: '#CD7F32', fontSize: '1.2rem' }} />; // Bronze
    return null;
  };

  const toggleRowExpansion = (puuid: string) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(puuid)) {
      newExpanded.delete(puuid);
    } else {
      newExpanded.add(puuid);
    }
    setExpandedRows(newExpanded);
  };

  const formatSeasonName = (seasonShort: string | null | undefined): string => {
    // Convert season_short like "e10a2" to "E10A2"
    if (!seasonShort) return 'N/A';
    return seasonShort.toUpperCase();
  };

  const renderPeakRankDetails = (entry: LeaderboardEntry) => {
    if (!entry.peak_rank) {
      return (
        <Typography variant="body2" color="text.secondary">
          Peak rank information not available
        </Typography>
      );
    }

    // Handle both legacy format (string) and new format (object)
    const isLegacyFormat = typeof entry.peak_rank === 'string';
    
    if (isLegacyFormat) {
      // Legacy format: peak_rank is a string, peak_season is separate
      const peakRankTier = entry.peak_rank as string;
      const peakSeason = entry.peak_season;
      
      return (
        <Box>
          <Typography variant="body1" fontWeight={600} sx={{ mb: 1 }}>
            Peak Rank Details
          </Typography>
          <Box display="flex" alignItems="center" gap={2}>
            <RankChip 
              label={peakRankTier} 
              rank={peakRankTier}
              size="small"
            />
            <Typography variant="body2" color="text.secondary">
              Season: {formatSeasonName(peakSeason)}
            </Typography>
          </Box>
        </Box>
      );
    } else {
      // New format: peak_rank is an object with tier_name, season_short, rr
      const peakRank = entry.peak_rank as PeakRank;
      
      return (
        <Box>
          <Typography variant="body1" fontWeight={600} sx={{ mb: 1 }}>
            Peak Rank Details
          </Typography>
          <Box display="flex" alignItems="center" gap={2}>
            <RankChip 
              label={peakRank.tier_name} 
              rank={peakRank.tier_name}
              size="small"
            />
            <Typography variant="body2" color="text.secondary">
              Season: {formatSeasonName(peakRank.season_short)}
            </Typography>
          </Box>
        </Box>
      );
    }
  };

  if (error) {
    return (
      <Alert severity="error" sx={{ margin: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Box>
      <StyledTableContainer>
        <Table stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell align="center">Rank</TableCell>
              <TableCell>Player</TableCell>
              <TableCell>Current Rank</TableCell>
              <TableCell align="center">ELO</TableCell>
              <TableCell align="center">Last Played</TableCell>
              <TableCell align="center">Tracker.gg</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              // Loading skeleton rows
              Array.from(new Array(perPage)).map((_, index) => (
                <TableRow key={index}>
                  <TableCell align="center">
                    <Skeleton variant="text" width={40} />
                  </TableCell>
                  <TableCell>
                    <Skeleton variant="text" width={120} />
                  </TableCell>
                  <TableCell>
                    <Skeleton variant="rounded" width={120} height={32} />
                  </TableCell>
                  <TableCell align="center">
                    <Skeleton variant="text" width={60} />
                  </TableCell>
                  <TableCell align="center">
                    <Skeleton variant="text" width={80} />
                  </TableCell>
                  <TableCell align="center">
                    <Skeleton variant="circular" width={24} height={24} />
                  </TableCell>
                </TableRow>
              ))
            ) : data && data.entries.length > 0 ? (
              data.entries.map((entry: LeaderboardEntry, index: number) => {
                const trackerUrl = `https://tracker.gg/valorant/profile/riot/${encodeURIComponent(entry.name)}%23${encodeURIComponent(entry.tag)}/overview`;
                const globalRank = calculateGlobalRank(currentPage, index);
                const isExpanded = expandedRows.has(entry.puuid);
                
                return (
                  <React.Fragment key={entry.puuid}>
                    <TableRow hover sx={{ cursor: 'pointer' }} onClick={() => toggleRowExpansion(entry.puuid)}>
                      <RankCell align="center">
                        <Box display="flex" alignItems="center" justifyContent="center" gap={1}>
                          {getRankIcon(globalRank)}
                          <Typography variant="h6" fontWeight={600} color="primary.main">
                            #{globalRank}
                          </Typography>
                        </Box>
                      </RankCell>
                      <TableCell>
                        <Box>
                          <Box display="flex" alignItems="baseline" gap={0.5}>
                            <Typography variant="body1" fontWeight={600}>
                              {entry.name}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              #{entry.tag}
                            </Typography>
                          </Box>
                          <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                            @{entry.discord_username}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <RankChip 
                          label={entry.current_tier || 'Unranked'} 
                          rank={entry.current_tier || 'Unranked'}
                          size="small"
                        />
                      </TableCell>
                      <EloCell align="center">
                        {entry.elo.toLocaleString()}
                      </EloCell>
                      <TableCell align="center">
                        <Typography variant="body2" color="text.secondary">
                          {formatLastPlayed(entry.last_played_match)}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Tooltip title="View on Tracker.gg" arrow>
                          <IconButton
                            component="a"
                            href={trackerUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            size="small"
                            onClick={(e) => e.stopPropagation()} // Prevent row expansion when clicking tracker link
                            sx={{ 
                              color: 'primary.main',
                              '&:hover': { 
                                color: 'primary.light',
                                backgroundColor: 'rgba(255, 70, 85, 0.1)'
                              }
                            }}
                          >
                            <OpenInNew fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell colSpan={6} sx={{ padding: 0, borderBottom: isExpanded ? 1 : 0 }}>
                        <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                          <Box sx={{ padding: 3, backgroundColor: 'rgba(0, 0, 0, 0.2)' }}>
                            {renderPeakRankDetails(entry)}
                          </Box>
                        </Collapse>
                      </TableCell>
                    </TableRow>
                  </React.Fragment>
                );
              })
            ) : (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <Typography variant="h6" color="text.secondary">
                    No leaderboard data available
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </StyledTableContainer>

      {data && data.total_pages > 1 && (
        <Box display="flex" justifyContent="center" alignItems="center" mt={3}>
          <Box display="flex" alignItems="center" gap={2}>
            <Typography variant="body2" color="text.secondary">
              Page {data.page} of {data.total_pages} ({data.total.toLocaleString()} players)
            </Typography>
            <Pagination
              count={data.total_pages}
              page={currentPage}
              onChange={handlePageChange}
              color="primary"
              size="large"
              showFirstButton
              showLastButton
            />
          </Box>
        </Box>
      )}
    </Box>
  );
};

export default LeaderboardTable;