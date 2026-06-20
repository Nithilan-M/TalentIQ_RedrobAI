import { useEffect } from "react";

export function useTheme() {
  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove("dark");
    localStorage.setItem("theme", "light");
  }, []);

  const toggleTheme = () => {
    // No-op to lock user into light white + red theme
  };

  return { theme: "light" as const, isDark: false, toggleTheme };
}
export default useTheme;
