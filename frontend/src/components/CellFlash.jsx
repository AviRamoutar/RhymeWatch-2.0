import React from "react";
import { motion, AnimatePresence } from "framer-motion";

export default function CellFlash({ value, children, className = "" }) {
  const prev = React.useRef(value);
  const [flashKey, setFlashKey] = React.useState(0);
  React.useEffect(() => {
    if (prev.current !== value && value != null) {
      setFlashKey((k) => k + 1);
      prev.current = value;
    }
  }, [value]);

  return (
    <span className={`relative inline-block ${className}`}>
      <AnimatePresence>
        <motion.span
          key={flashKey}
          className="absolute inset-0 rounded"
          initial={{ backgroundColor: "rgba(245,158,11,0.25)" }}
          animate={{ backgroundColor: "rgba(245,158,11,0)" }}
          transition={{ duration: 0.6, ease: "easeOut" }}
        />
      </AnimatePresence>
      <span className="relative">{children}</span>
    </span>
  );
}
