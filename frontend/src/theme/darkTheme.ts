import { createTheme, ThemeOptions } from '@mui/material/styles';

// Valorant color palette
const valorantColors = {
  primary: {
    main: '#ff4655', // Valorant red
    light: '#ff6a73',
    dark: '#e73c47',
    contrastText: '#ffffff',
  },
  secondary: {
    main: '#1f2326', // Dark grey
    light: '#353a3f',
    dark: '#0f1419',
    contrastText: '#ffffff',
  },
  background: {
    default: '#0f1419', // Very dark background
    paper: '#1f2326', // Card background
    elevation1: '#2a2f35', // Slightly lighter for elevated components
  },
  surface: {
    main: '#2a2f35',
    light: '#3a4047',
    dark: '#1a1f25',
  },
  text: {
    primary: '#ece8e1', // Light cream
    secondary: '#9aa0a6', // Medium grey
    disabled: '#5f6368', // Darker grey
  },
  ranks: {
    iron: '#4a4a4a',
    bronze: '#cd7f32',
    silver: '#c0c0c0',
    gold: '#ffd700',
    platinum: '#00ffff',
    diamond: '#b566d9',
    ascendant: '#32cd32',
    immortal: '#ff6b6b',
    radiant: '#ffffff',
  },
};

const themeOptions: ThemeOptions = {
  palette: {
    mode: 'dark',
    primary: valorantColors.primary,
    secondary: valorantColors.secondary,
    background: valorantColors.background,
    text: valorantColors.text,
    error: {
      main: '#ff4444',
    },
    warning: {
      main: '#ff9800',
    },
    success: {
      main: '#4caf50',
    },
    info: {
      main: '#2196f3',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 600,
      color: valorantColors.text.primary,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 500,
      color: valorantColors.text.primary,
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 500,
      color: valorantColors.text.primary,
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 500,
      color: valorantColors.text.primary,
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 500,
      color: valorantColors.text.primary,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 500,
      color: valorantColors.text.primary,
    },
    body1: {
      color: valorantColors.text.primary,
    },
    body2: {
      color: valorantColors.text.secondary,
    },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: valorantColors.background.default,
          scrollbarWidth: 'thin',
          scrollbarColor: `${valorantColors.primary.main} ${valorantColors.background.paper}`,
          '&::-webkit-scrollbar': {
            width: '6px',
          },
          '&::-webkit-scrollbar-track': {
            backgroundColor: valorantColors.background.paper,
          },
          '&::-webkit-scrollbar-thumb': {
            backgroundColor: valorantColors.primary.main,
            borderRadius: '3px',
          },
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: valorantColors.background.paper,
          boxShadow: `0 2px 8px ${valorantColors.primary.main}20`,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundColor: valorantColors.background.paper,
          backgroundImage: 'none',
        },
        elevation1: {
          backgroundColor: valorantColors.background.elevation1,
        },
      },
    },
    MuiTableContainer: {
      styleOverrides: {
        root: {
          backgroundColor: valorantColors.background.paper,
        },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: {
          '& .MuiTableCell-head': {
            backgroundColor: valorantColors.surface.main,
            color: valorantColors.text.primary,
            fontWeight: 600,
            borderBottom: `2px solid ${valorantColors.primary.main}`,
          },
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          '&:nth-of-type(odd)': {
            backgroundColor: valorantColors.background.paper,
          },
          '&:nth-of-type(even)': {
            backgroundColor: valorantColors.surface.main,
          },
          '&:hover': {
            backgroundColor: `${valorantColors.primary.main}10`,
          },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: `1px solid ${valorantColors.surface.light}`,
          color: valorantColors.text.primary,
        },
      },
    },
    MuiPagination: {
      styleOverrides: {
        root: {
          '& .MuiPaginationItem-root': {
            color: valorantColors.text.primary,
            borderColor: valorantColors.surface.light,
          },
          '& .Mui-selected': {
            backgroundColor: `${valorantColors.primary.main} !important`,
            color: valorantColors.primary.contrastText,
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 500,
        },
      },
    },
  },
};

export const darkTheme = createTheme(themeOptions);

// Helper function to get rank color
export const getRankColor = (rank: string): string => {
  const rankLower = rank.toLowerCase();
  
  if (rankLower.includes('iron')) return valorantColors.ranks.iron;
  if (rankLower.includes('bronze')) return valorantColors.ranks.bronze;
  if (rankLower.includes('silver')) return valorantColors.ranks.silver;
  if (rankLower.includes('gold')) return valorantColors.ranks.gold;
  if (rankLower.includes('platinum')) return valorantColors.ranks.platinum;
  if (rankLower.includes('diamond')) return valorantColors.ranks.diamond;
  if (rankLower.includes('ascendant')) return valorantColors.ranks.ascendant;
  if (rankLower.includes('immortal')) return valorantColors.ranks.immortal;
  if (rankLower.includes('radiant')) return valorantColors.ranks.radiant;
  
  return valorantColors.text.secondary; // Default
};

export default darkTheme;