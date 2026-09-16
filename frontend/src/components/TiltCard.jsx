import { useRef } from 'react';
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion';
import { Paper } from '@mui/material';

/**
 * A Paper surface that tilts in 3D toward the cursor and lifts on hover.
 * This is the platform's signature motion device — used for stat cards,
 * course cards, and other glanceable surfaces, not every element.
 */
export default function TiltCard({ children, sx, tiltStrength = 10, onClick, ...rest }) {
  const ref = useRef(null);

  const x = useMotionValue(0);
  const y = useMotionValue(0);

  const rotateX = useSpring(useTransform(y, [-0.5, 0.5], [tiltStrength, -tiltStrength]), {
    stiffness: 300,
    damping: 25,
  });
  const rotateY = useSpring(useTransform(x, [-0.5, 0.5], [-tiltStrength, tiltStrength]), {
    stiffness: 300,
    damping: 25,
  });

  const handleMouseMove = (e) => {
    const rect = ref.current.getBoundingClientRect();
    x.set((e.clientX - rect.left) / rect.width - 0.5);
    y.set((e.clientY - rect.top) / rect.height - 0.5);
  };

  const handleMouseLeave = () => {
    x.set(0);
    y.set(0);
  };

  return (
    <motion.div
      ref={ref}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      onClick={onClick}
      style={{
        rotateX,
        rotateY,
        transformPerspective: 800,
        cursor: onClick ? 'pointer' : 'default',
      }}
      whileHover={{ y: -4, scale: 1.01 }}
      transition={{ type: 'spring', stiffness: 300, damping: 22 }}
    >
      <Paper
        elevation={2}
        sx={{
          p: 3,
          height: '100%',
          transition: 'box-shadow 0.25s ease, border-color 0.25s ease',
          border: '1px solid',
          borderColor: 'divider',
          '&:hover': {
            boxShadow: '0 16px 36px rgba(67, 56, 202, 0.16)',
            borderColor: 'primary.light',
          },
          ...sx,
        }}
        {...rest}
      >
        {children}
      </Paper>
    </motion.div>
  );
}
