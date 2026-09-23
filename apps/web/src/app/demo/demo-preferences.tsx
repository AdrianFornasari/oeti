"use client";

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

export type DemoLanguage = "en" | "es";
export type DemoTheme = "light" | "dark";

type DemoPreferencesContextValue = {
  language: DemoLanguage;
  theme: DemoTheme;
  setLanguage: (language: DemoLanguage) => void;
  setTheme: (theme: DemoTheme) => void;
  isSpanish: boolean;
};

const DemoPreferencesContext = createContext<DemoPreferencesContextValue | null>(null);

const LANGUAGE_KEY = "oeti-demo-language";
const THEME_KEY = "oeti-demo-theme";

export function DemoPreferencesProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<DemoLanguage>("en");
  const [theme, setTheme] = useState<DemoTheme>("light");

  useEffect(() => {
    const storedLanguage = window.localStorage.getItem(LANGUAGE_KEY);
    const storedTheme = window.localStorage.getItem(THEME_KEY);

    if (storedLanguage === "en" || storedLanguage === "es") setLanguage(storedLanguage);
    if (storedTheme === "light" || storedTheme === "dark") setTheme(storedTheme);
  }, []);

  useEffect(() => {
    window.localStorage.setItem(LANGUAGE_KEY, language);
    document.documentElement.lang = language === "es" ? "es" : "en";
  }, [language]);

  useEffect(() => {
    window.localStorage.setItem(THEME_KEY, theme);
    document.documentElement.dataset.demoTheme = theme;
    document.documentElement.style.colorScheme = theme;
  }, [theme]);

  const value = useMemo(
    () => ({ language, theme, setLanguage, setTheme, isSpanish: language === "es" }),
    [language, theme],
  );

  return <DemoPreferencesContext.Provider value={value}>{children}</DemoPreferencesContext.Provider>;
}

export function useDemoPreferences() {
  const context = useContext(DemoPreferencesContext);
  if (!context) throw new Error("useDemoPreferences must be used within DemoPreferencesProvider");
  return context;
}
