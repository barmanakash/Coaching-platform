import { motion } from 'framer-motion';

/**
 * Wraps page content with a single, quiet entrance animation on mount.
 * Used once per page — not layered with other motion.
 */
export default function PageFade({ children }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}
