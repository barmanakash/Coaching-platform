import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#4338CA',
      light: '#6366F1',
      dark: '#241E66',
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: '#F59E0B',
      light: '#FBBF24',
      dark: '#B45309',
      contrastText: '#1E1B0F',
    },
    success: {
      main: '#059669',
    },
    background: {
      // A soft indigo-tinted neutral instead of flat white — keeps cards
      // and surfaces feeling deliberate rather than washed out.
      default: '#F1F1FA',
      paper: '#FFFFFF',
    },
    text: {
      primary: '#0F172A',
      secondary: '#64748B',
    },
    divider: '#E4E4F0',
    navy: {
      main: '#1E1B4B',
      dark: '#15132F',
      light: '#312E81',
    },
  },
  shape: {
    borderRadius: 12,
  },
  typography: {
    fontFamily: ['Inter', 'Helvetica', 'Arial', 'sans-serif'].join(','),
    fontSize: 13.5,
    h1: { fontFamily: "'Manrope', sans-serif", fontWeight: 800, fontSize: '2.25rem', letterSpacing: '-0.02em', lineHeight: 1.2 },
    h2: { fontFamily: "'Manrope', sans-serif", fontWeight: 800, fontSize: '1.875rem', letterSpacing: '-0.02em', lineHeight: 1.25 },
    h3: { fontFamily: "'Manrope', sans-serif", fontWeight: 700, fontSize: '1.5rem', letterSpacing: '-0.01em', lineHeight: 1.3 },
    h4: { fontFamily: "'Manrope', sans-serif", fontWeight: 700, fontSize: '1.375rem', letterSpacing: '-0.01em', lineHeight: 1.3 },
    h5: { fontFamily: "'Manrope', sans-serif", fontWeight: 700, fontSize: '1.125rem', lineHeight: 1.35 },
    h6: { fontFamily: "'Manrope', sans-serif", fontWeight: 600, fontSize: '1rem', lineHeight: 1.4 },
    subtitle1: { fontSize: '0.9375rem', fontWeight: 500 },
    subtitle2: { fontSize: '0.8125rem', fontWeight: 600 },
    body1: { fontSize: '0.875rem' },
    body2: { fontSize: '0.8125rem' },
    caption: { fontSize: '0.75rem' },
    button: { textTransform: 'none', fontWeight: 600, fontFamily: "'Manrope', sans-serif", fontSize: '0.875rem' },
  },
  shadows: [
    'none',
    '0 1px 2px rgba(30, 27, 75, 0.06)',
    '0 1px 3px rgba(30, 27, 75, 0.08)',
    '0 2px 6px rgba(30, 27, 75, 0.08)',
    '0 4px 10px rgba(30, 27, 75, 0.10)',
    '0 6px 16px rgba(30, 27, 75, 0.10)',
    '0 8px 20px rgba(30, 27, 75, 0.12)',
    '0 10px 24px rgba(30, 27, 75, 0.12)',
    '0 12px 28px rgba(30, 27, 75, 0.14)',
    '0 14px 32px rgba(30, 27, 75, 0.14)',
    '0 16px 36px rgba(30, 27, 75, 0.16)',
    '0 18px 40px rgba(30, 27, 75, 0.16)',
    '0 20px 44px rgba(30, 27, 75, 0.18)',
    '0 22px 48px rgba(30, 27, 75, 0.18)',
    '0 24px 52px rgba(30, 27, 75, 0.20)',
    '0 26px 56px rgba(30, 27, 75, 0.20)',
    '0 28px 60px rgba(30, 27, 75, 0.22)',
    '0 30px 64px rgba(30, 27, 75, 0.22)',
    '0 32px 68px rgba(30, 27, 75, 0.24)',
    '0 34px 72px rgba(30, 27, 75, 0.24)',
    '0 36px 76px rgba(30, 27, 75, 0.26)',
    '0 38px 80px rgba(30, 27, 75, 0.26)',
    '0 40px 84px rgba(30, 27, 75, 0.28)',
    '0 42px 88px rgba(30, 27, 75, 0.28)',
    '0 44px 92px rgba(30, 27, 75, 0.30)',
  ],
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        '*': { boxSizing: 'border-box' },
        body: {
          backgroundColor: '#F1F1FA',
          backgroundImage:
            'radial-gradient(circle at 100% 0%, rgba(67,56,202,0.05) 0%, rgba(67,56,202,0) 45%), ' +
            'radial-gradient(circle at 0% 100%, rgba(245,158,11,0.05) 0%, rgba(245,158,11,0) 45%)',
          backgroundAttachment: 'fixed',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          padding: '9px 20px',
          transition: 'transform 0.15s ease, box-shadow 0.15s ease',
        },
        contained: {
          boxShadow: '0 2px 8px rgba(67, 56, 202, 0.24)',
          '&:hover': {
            boxShadow: '0 6px 16px rgba(67, 56, 202, 0.32)',
            transform: 'translateY(-1px)',
          },
          '&:active': { transform: 'translateY(0)' },
        },
        outlined: {
          '&:hover': { transform: 'translateY(-1px)' },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: { backgroundImage: 'none' },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: { fontWeight: 600, borderRadius: 8 },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          transition: 'background-color 0.15s ease',
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          transition: 'background-color 0.2s ease, color 0.2s ease',
        },
      },
    },
  },
});

export default theme;
