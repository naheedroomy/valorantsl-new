import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Stepper,
  Step,
  StepLabel,
  Card,
  CardContent,
  Divider,
  List,
  ListItem,
  ListItemText,
  Chip
} from '@mui/material';
import { styled } from '@mui/material/styles';
import { 
  Login as LoginIcon, 
  Search as SearchIcon, 
  PersonAdd as PersonAddIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  SportsEsports as SportsEsportsIcon
} from '@mui/icons-material';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const StyledPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(4),
  marginTop: theme.spacing(4),
  marginBottom: theme.spacing(4),
  background: 'linear-gradient(135deg, #1f2326 0%, #2a2f35 100%)',
  boxShadow: `0 8px 32px ${theme.palette.primary.main}20`,
  border: `1px solid ${theme.palette.primary.main}30`,
}));

const StyledButton = styled(Button)(({ theme }) => ({
  marginTop: theme.spacing(2),
  padding: theme.spacing(1.5, 4),
  fontSize: '1.1rem',
  fontWeight: 600,
  background: `linear-gradient(45deg, ${theme.palette.primary.main} 30%, ${theme.palette.primary.light} 90%)`,
  boxShadow: `0 3px 5px 2px ${theme.palette.primary.main}30`,
  '&:hover': {
    boxShadow: `0 5px 10px 3px ${theme.palette.primary.main}40`,
  },
}));

const PlayerCard = styled(Card)(({ theme }) => ({
  marginTop: theme.spacing(3),
  background: theme.palette.background.paper,
  border: `1px solid ${theme.palette.primary.main}50`,
  '& .MuiCardContent-root': {
    padding: theme.spacing(3),
  }
}));

interface DiscordUser {
  discord_id: number;
  discord_username: string;
  discord_discriminator: string;
  discord_avatar: string | null;
  discord_email: string | null;
  access_token: string;
}

interface PlayerPreview {
  puuid: string;
  name: string;
  tag: string;
  current_rank: string;
  elo: number;
  peak_rank: string;
  peak_season: string;
  last_played: string | null;
}

const Registration: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  // Step management
  const [activeStep, setActiveStep] = useState(0);
  const steps = ['Discord Authentication', 'Enter PUUID', 'Confirm Registration'];
  
  // State
  const [discordUser, setDiscordUser] = useState<DiscordUser | null>(null);
  const [puuid, setPuuid] = useState('');
  const [playerPreview, setPlayerPreview] = useState<PlayerPreview | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [processedCode, setProcessedCode] = useState<string | null>(null);

  // Restore Discord user from sessionStorage on mount
  useEffect(() => {
    const storedUser = sessionStorage.getItem('discord_user');
    if (storedUser && !discordUser) {
      try {
        const parsedUser = JSON.parse(storedUser);
        setDiscordUser(parsedUser);
        setActiveStep(1);
      } catch (err) {
        console.error('Failed to parse stored Discord user:', err);
        sessionStorage.removeItem('discord_user');
      }
    }
  }, []);

  // Handle Discord OAuth callback
  useEffect(() => {
    const code = searchParams.get('code');
    if (code && activeStep === 0 && !discordUser && !loading && processedCode !== code) {
      setProcessedCode(code);
      handleDiscordCallback(code);
    }
  }, [searchParams, activeStep, discordUser, loading, processedCode]);

  const handleDiscordLogin = async () => {
    try {
      setError(null);
      const response = await fetch(`${API_URL}/api/v1/auth/discord/login`);
      const data = await response.json();
      
      if (data.url) {
        window.location.href = data.url;
      }
    } catch (err) {
      setError('Failed to initiate Discord login');
      console.error('Discord login error:', err);
    }
  };

  const handleDiscordCallback = async (code: string) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`${API_URL}/api/v1/auth/discord/callback?code=${code}`);
      
      if (!response.ok) {
        // If code already used (409), silently ignore - likely duplicate request
        if (response.status === 409) {
          window.history.replaceState({}, document.title, '/register');
          setLoading(false);
          return;
        }
        
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to authenticate with Discord');
        // Clear the URL params on error
        window.history.replaceState({}, document.title, '/register');
        setLoading(false);
        return;
      }
      
      const data = await response.json();
      
      if (data.exists) {
        setError(`This Discord account is already registered as ${data.existing_data.name}#${data.existing_data.tag}. Each Discord account can only be linked to one Valorant account. If you need to update your PUUID or have issues with your registration, please contact an administrator.`);
        // Clear the URL params on error
        window.history.replaceState({}, document.title, '/register');
        setLoading(false);
        return;
      }
      
      if (data.user) {
        setDiscordUser(data.user);
        setActiveStep(1);
        // Store in sessionStorage to persist across re-renders
        sessionStorage.setItem('discord_user', JSON.stringify(data.user));
        // Clear the URL params after successful auth
        window.history.replaceState({}, document.title, '/register');
      } else {
        setError('No user data received from Discord');
        window.history.replaceState({}, document.title, '/register');
      }
    } catch (err) {
      setError('Failed to authenticate with Discord');
      console.error('Discord callback error:', err);
      // Clear the URL params on error
      window.history.replaceState({}, document.title, '/register');
    } finally {
      setLoading(false);
    }
  };

  const handlePuuidSubmit = async () => {
    if (!puuid) {
      setError('Please enter your PUUID');
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      
      // Check if PUUID exists
      const checkResponse = await fetch(`${API_URL}/api/v1/auth/check-puuid`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ puuid })
      });
      
      const checkData = await checkResponse.json();
      
      if (checkData.exists) {
        setError(`This PUUID is already registered to ${checkData.user.name}#${checkData.user.tag}. Each player can only register once. If this is your account and you need to update your Discord connection, please contact an administrator.`);
        setLoading(false);
        return;
      }
      
      // Get player preview
      const previewResponse = await fetch(`${API_URL}/api/v1/register/preview`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ puuid })
      });
      
      if (previewResponse.status === 404) {
        setError('Player not found. Please check your PUUID.');
        setLoading(false);
        return;
      }
      
      if (previewResponse.status === 409) {
        setError('This player is already registered.');
        setLoading(false);
        return;
      }
      
      const previewData = await previewResponse.json();
      setPlayerPreview(previewData);
      setActiveStep(2);
      
    } catch (err) {
      setError('Failed to fetch player data');
      console.error('PUUID submit error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFinalSubmit = async () => {
    if (!discordUser || !playerPreview) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`${API_URL}/api/v1/register/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          discord_id: discordUser.discord_id,
          discord_username: discordUser.discord_username,
          puuid: playerPreview.puuid
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        
        // Handle specific error cases with user-friendly messages
        let errorMessage = 'Registration failed';
        
        if (response.status === 409) {
          // Conflict - Discord user already registered
          if (errorData.message && errorData.message.includes('Discord user already registered')) {
            errorMessage = `This Discord account is already registered in the system. Each Discord account can only be linked to one PUUID. If you need to update your PUUID, please contact an administrator.`;
          } else if (errorData.message && errorData.message.includes('already registered')) {
            errorMessage = errorData.message;
          } else {
            errorMessage = 'This account or PUUID is already registered.';
          }
        } else if (response.status === 404) {
          errorMessage = 'Player not found. Please verify your PUUID is correct.';
        } else if (response.status === 400) {
          errorMessage = errorData.detail || errorData.message || 'Invalid registration data. Please check your information.';
        } else if (response.status === 500) {
          errorMessage = 'Server error occurred. Please try again later or contact support if the issue persists.';
        } else {
          errorMessage = errorData.detail || errorData.message || 'Registration failed. Please try again.';
        }
        
        setError(errorMessage);
        setLoading(false);
        return;
      }
      
      const data = await response.json();
      setSuccess(true);
      
      // Clear session storage
      sessionStorage.removeItem('discord_user');
      
      // Redirect to leaderboard after 3 seconds
      setTimeout(() => {
        navigate('/');
      }, 3000);
      
    } catch (err) {
      setError('Failed to complete registration');
      console.error('Registration submit error:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatLastPlayed = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
      
      if (diffDays === 0) return 'Today';
      if (diffDays === 1) return 'Yesterday';
      if (diffDays < 7) return `${diffDays} days ago`;
      
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
      });
    } catch {
      return 'N/A';
    }
  };

  const getRankColor = (rank: string) => {
    const rankLower = rank.toLowerCase();
    if (rankLower.includes('iron')) return '#4a4a4a';
    if (rankLower.includes('bronze')) return '#cd7f32';
    if (rankLower.includes('silver')) return '#c0c0c0';
    if (rankLower.includes('gold')) return '#ffd700';
    if (rankLower.includes('platinum')) return '#00ffff';
    if (rankLower.includes('diamond')) return '#b566d9';
    if (rankLower.includes('ascendant')) return '#32cd32';
    if (rankLower.includes('immortal')) return '#ff6b6b';
    if (rankLower.includes('radiant')) return '#ffffff';
    return '#9aa0a6';
  };

  if (success) {
    return (
      <Container maxWidth="sm">
        <StyledPaper>
          <Box display="flex" flexDirection="column" alignItems="center">
            <CheckCircleIcon sx={{ fontSize: 80, color: 'success.main', mb: 2 }} />
            <Typography variant="h4" gutterBottom>
              Registration Successful!
            </Typography>
            <Typography variant="body1" color="text.secondary" align="center">
              Welcome to ValorantSL! You've been added to the leaderboard.
            </Typography>
            <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 2 }}>
              Redirecting to leaderboard...
            </Typography>
          </Box>
        </StyledPaper>
      </Container>
    );
  }

  return (
    <Container maxWidth="md">
      <StyledPaper>
        <Typography variant="h3" gutterBottom align="center" sx={{ mb: 4 }}>
          Join ValorantSL Leaderboard
        </Typography>
        
        <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {error && (
          <Alert 
            severity="error" 
            sx={{ 
              mb: 3,
              '& .MuiAlert-message': {
                fontSize: '1rem',
                lineHeight: 1.6
              }
            }} 
            onClose={() => setError(null)}
            icon={<ErrorIcon fontSize="large" />}
          >
            <Typography variant="body1" component="div">
              {error}
            </Typography>
          </Alert>
        )}

        {/* Step 1: Discord Authentication */}
        {activeStep === 0 && (
          <Box display="flex" flexDirection="column" alignItems="center">
            <LoginIcon sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
            <Typography variant="h5" gutterBottom>
              Connect Your Discord Account
            </Typography>
            <Typography variant="body1" color="text.secondary" align="center" sx={{ mb: 3 }}>
              We use Discord for authentication and to display your username on the leaderboard.
            </Typography>
            
            <StyledButton
              variant="contained"
              size="large"
              startIcon={<LoginIcon />}
              onClick={handleDiscordLogin}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Login with Discord'}
            </StyledButton>
          </Box>
        )}

        {/* Step 2: Enter PUUID */}
        {activeStep === 1 && discordUser && (
          <Box>
            <Box display="flex" alignItems="center" mb={3}>
              <Typography variant="h6" sx={{ flexGrow: 1 }}>
                Welcome, {discordUser.discord_username}!
              </Typography>
              <Chip label="Discord Connected" color="success" />
              <Button 
                size="small" 
                onClick={() => {
                  sessionStorage.removeItem('discord_user');
                  setDiscordUser(null);
                  setActiveStep(0);
                  setError(null);
                }}
                sx={{ ml: 2 }}
              >
                Change Account
              </Button>
            </Box>
            
            <Divider sx={{ mb: 3 }} />
            
            <Typography variant="h5" gutterBottom>
              Enter Your Riot PUUID
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
              Your PUUID (Player Universally Unique Identifier) is required to fetch your Valorant stats.
              You can find it on tracker.gg or other Valorant stats websites.
            </Typography>
            
            <TextField
              fullWidth
              label="PUUID"
              placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
              value={puuid}
              onChange={(e) => setPuuid(e.target.value)}
              variant="outlined"
              sx={{ mb: 2 }}
            />
            
            <Box display="flex" justifyContent="flex-end">
              <StyledButton
                variant="contained"
                startIcon={<SearchIcon />}
                onClick={handlePuuidSubmit}
                disabled={loading || !puuid}
              >
                {loading ? <CircularProgress size={24} /> : 'Verify Player'}
              </StyledButton>
            </Box>
          </Box>
        )}

        {/* Step 3: Confirm Registration */}
        {activeStep === 2 && playerPreview && (
          <Box>
            <Typography variant="h5" gutterBottom>
              Confirm Your Registration
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
              Please verify this is your account before completing registration.
            </Typography>
            
            <PlayerCard>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <SportsEsportsIcon sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h4">
                    {playerPreview.name}#{playerPreview.tag}
                  </Typography>
                </Box>
                
                <List>
                  <ListItem>
                    <ListItemText 
                      primary="Current Rank"
                      secondary={
                        <Chip 
                          label={playerPreview.current_rank}
                          sx={{ 
                            backgroundColor: getRankColor(playerPreview.current_rank),
                            color: '#fff',
                            fontWeight: 600
                          }}
                        />
                      }
                    />
                  </ListItem>
                  
                  <ListItem>
                    <ListItemText 
                      primary="ELO"
                      secondary={playerPreview.elo || 'Unranked'}
                    />
                  </ListItem>
                  
                  <ListItem>
                    <ListItemText 
                      primary="Peak Rank"
                      secondary={`${playerPreview.peak_rank} (${playerPreview.peak_season})`}
                    />
                  </ListItem>
                  
                  <ListItem>
                    <ListItemText 
                      primary="Last Played"
                      secondary={formatLastPlayed(playerPreview.last_played)}
                    />
                  </ListItem>
                  
                  <ListItem>
                    <ListItemText 
                      primary="Discord"
                      secondary={discordUser?.discord_username || 'N/A'}
                    />
                  </ListItem>
                </List>
              </CardContent>
            </PlayerCard>
            
            <Box display="flex" justifyContent="space-between" mt={3}>
              <Button
                variant="outlined"
                onClick={() => {
                  setActiveStep(1);
                  setPlayerPreview(null);
                  setPuuid('');
                }}
              >
                Use Different PUUID
              </Button>
              
              <StyledButton
                variant="contained"
                startIcon={<PersonAddIcon />}
                onClick={handleFinalSubmit}
                disabled={loading}
              >
                {loading ? <CircularProgress size={24} /> : 'Add to Leaderboard'}
              </StyledButton>
            </Box>
          </Box>
        )}
      </StyledPaper>
    </Container>
  );
};

export default Registration;