import {
  AppBar, Toolbar, Typography, Drawer, List, Box, Button, Avatar,
} from '@mui/material';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import LogoutIcon from '@mui/icons-material/Logout';
import { useAuth } from '../context/AuthContext';
import PageFade from '../components/PageFade';

const DRAWER_WIDTH = 260;
const NAVY = '#1E1B4B';
const NAVY_DARK = '#15132F';

/**
 * Shared shell for role-based dashboards (Admin/Teacher/Student).
 * Dark indigo chrome (sidebar + topbar) matches the auth screens'
 * identity; content area sits on the app's tinted background.
 */
export default function DashboardLayout({ title, navItems }) {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          zIndex: (theme) => theme.zIndex.drawer + 1,
          background: `linear-gradient(90deg, ${NAVY_DARK}, ${NAVY})`,
          color: '#FFFFFF',
          borderBottom: '1px solid rgba(255,255,255,0.08)',
        }}
      >
        <Toolbar sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Typography variant="h6" noWrap sx={{ color: '#FFFFFF' }}>{title}</Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Avatar
              sx={{
                width: 34, height: 34, fontSize: 14, fontWeight: 700,
                bgcolor: 'secondary.main', color: 'secondary.contrastText',
              }}
            >
              {user?.name?.[0]?.toUpperCase() || '?'}
            </Avatar>
            <Box sx={{ display: { xs: 'none', sm: 'block' } }}>
              <Typography variant="body2" fontWeight={600} lineHeight={1.2}>{user?.name}</Typography>
              <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.65)', textTransform: 'capitalize' }}>
                {user?.role}
              </Typography>
            </Box>
            <Button
              onClick={handleLogout}
              startIcon={<LogoutIcon fontSize="small" />}
              sx={{
                ml: 1, color: '#FFFFFF', bgcolor: 'rgba(255,255,255,0.08)',
                '&:hover': { bgcolor: 'rgba(255,255,255,0.16)' },
              }}
            >
              Logout
            </Button>
          </Box>
        </Toolbar>
      </AppBar>

      <Drawer
        variant="permanent"
        sx={{
          width: DRAWER_WIDTH,
          flexShrink: 0,
          [`& .MuiDrawer-paper`]: {
            width: DRAWER_WIDTH,
            boxSizing: 'border-box',
            border: 'none',
            background: `linear-gradient(180deg, ${NAVY}, ${NAVY_DARK})`,
          },
        }}
      >
        <Toolbar />
        <List sx={{ px: 1.5, py: 2, position: 'relative' }}>
          {navItems.map((item) => {
            const selected = location.pathname === item.path;
            return (
              <Box
                key={item.path}
                onClick={() => navigate(item.path)}
                sx={{
                  position: 'relative',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1.5,
                  px: 2,
                  py: 1.25,
                  mb: 0.5,
                  borderRadius: 2.5,
                  cursor: 'pointer',
                  color: selected ? '#FFFFFF' : 'rgba(255,255,255,0.62)',
                  fontWeight: selected ? 700 : 500,
                  zIndex: 1,
                  transition: 'color 0.2s ease',
                  '&:hover': { color: '#FFFFFF' },
                }}
              >
                {selected && (
                  <motion.div
                    layoutId="nav-pill"
                    transition={{ type: 'spring', stiffness: 400, damping: 32 }}
                    style={{
                      position: 'absolute',
                      inset: 0,
                      borderRadius: 12,
                      background: 'linear-gradient(135deg, rgba(99,102,241,0.55), rgba(245,158,11,0.28))',
                      boxShadow: '0 4px 14px rgba(0,0,0,0.25)',
                      zIndex: -1,
                    }}
                  />
                )}
                <Typography variant="body2" sx={{ fontWeight: 'inherit' }}>{item.label}</Typography>
              </Box>
            );
          })}
        </List>
      </Drawer>

      <Box component="main" sx={{ flexGrow: 1, p: 3, bgcolor: 'background.default' }}>
        <Toolbar />
        <PageFade key={location.pathname}>
          <Outlet />
        </PageFade>
      </Box>
    </Box>
  );
}
