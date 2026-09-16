import { Box, keyframes } from '@mui/material';

const drift1 = keyframes`
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(40px, -30px) scale(1.08); }
`;
const drift2 = keyframes`
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(-50px, 40px) scale(1.1); }
`;

/**
 * Shared full-screen backdrop for Login/Signup: a slow-drifting aurora
 * gradient behind a glass card. This is the one "hero" motion moment
 * every user sees, reserved for the entry point only.
 */
export default function AuthShell({ children }) {
  return (
    <Box
      sx={{
        minHeight: '100vh',
        position: 'relative',
        overflow: 'hidden',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        py: 4,
        background: 'linear-gradient(160deg, #1E1B4B 0%, #312E81 45%, #3730A3 100%)',
      }}
    >
      <Box
        sx={{
          position: 'absolute',
          width: 520,
          height: 520,
          borderRadius: '50%',
          top: '-10%',
          left: '-8%',
          background: 'radial-gradient(circle, rgba(99,102,241,0.55) 0%, rgba(99,102,241,0) 70%)',
          animation: `${drift1} 14s ease-in-out infinite`,
          filter: 'blur(10px)',
        }}
      />
      <Box
        sx={{
          position: 'absolute',
          width: 460,
          height: 460,
          borderRadius: '50%',
          bottom: '-12%',
          right: '-6%',
          background: 'radial-gradient(circle, rgba(245,158,11,0.35) 0%, rgba(245,158,11,0) 70%)',
          animation: `${drift2} 16s ease-in-out infinite`,
          filter: 'blur(10px)',
        }}
      />
      <Box
        sx={{
          position: 'absolute',
          width: 360,
          height: 360,
          borderRadius: '50%',
          top: '35%',
          right: '20%',
          background: 'radial-gradient(circle, rgba(129,140,248,0.30) 0%, rgba(129,140,248,0) 70%)',
          animation: `${drift1} 20s ease-in-out infinite`,
          filter: 'blur(14px)',
        }}
      />

      <Box sx={{ position: 'relative', zIndex: 1 }}>
        {children}
      </Box>
    </Box>
  );
}
