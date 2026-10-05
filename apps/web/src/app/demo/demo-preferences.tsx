"use client";

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

export type DemoLanguage = "en" | "es";
export type DemoTheme = "light" | "dark";
export const DEMO_FONT_SCALES = [0.9, 1, 1.1, 1.2, 1.3] as const;
export type DemoFontScale = (typeof DEMO_FONT_SCALES)[number];

type DemoPreferencesContextValue = {
  language: DemoLanguage;
  theme: DemoTheme;
  fontScale: DemoFontScale;
  setLanguage: (language: DemoLanguage) => void;
  setTheme: (theme: DemoTheme) => void;
  setFontScale: (fontScale: DemoFontScale) => void;
  isSpanish: boolean;
};

const DemoPreferencesContext = createContext<DemoPreferencesContextValue | null>(null);

const LANGUAGE_KEY = "oeti-demo-language";
const THEME_KEY = "oeti-demo-theme";
const FONT_SCALE_KEY = "oeti-demo-font-scale";

function isDemoFontScale(value: number): value is DemoFontScale {
  return DEMO_FONT_SCALES.includes(value as DemoFontScale);
}

export function DemoPreferencesProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<DemoLanguage>("es");
  const [theme, setTheme] = useState<DemoTheme>("light");
  const [fontScale, setFontScale] = useState<DemoFontScale>(1);
  const [preferencesLoaded, setPreferencesLoaded] = useState(false);

  useEffect(() => {
    const storedLanguage = window.localStorage.getItem(LANGUAGE_KEY);
    const storedTheme = window.localStorage.getItem(THEME_KEY);
    const storedFontScale = Number(window.localStorage.getItem(FONT_SCALE_KEY));

    const initialLanguage: DemoLanguage = storedLanguage === "en" || storedLanguage === "es" ? storedLanguage : "es";
    const initialTheme: DemoTheme = storedTheme === "light" || storedTheme === "dark" ? storedTheme : "light";
    const initialFontScale: DemoFontScale = isDemoFontScale(storedFontScale) ? storedFontScale : 1;

    setLanguage(initialLanguage);
    setTheme(initialTheme);
    setFontScale(initialFontScale);
    document.documentElement.lang = initialLanguage === "es" ? "es" : "en";
    document.documentElement.dataset.demoTheme = initialTheme;
    document.documentElement.style.colorScheme = initialTheme;
    setPreferencesLoaded(true);
  }, []);

  useEffect(() => {
    if (!preferencesLoaded) return;
    window.localStorage.setItem(LANGUAGE_KEY, language);
    document.documentElement.lang = language === "es" ? "es" : "en";
  }, [language, preferencesLoaded]);

  useEffect(() => {
    if (!preferencesLoaded) return;
    window.localStorage.setItem(THEME_KEY, theme);
    document.documentElement.dataset.demoTheme = theme;
    document.documentElement.style.colorScheme = theme;
  }, [theme, preferencesLoaded]);

  useEffect(() => {
    if (!preferencesLoaded) return;
    window.localStorage.setItem(FONT_SCALE_KEY, String(fontScale));
  }, [fontScale, preferencesLoaded]);

  const value = useMemo(
    () => ({ language, theme, fontScale, setLanguage, setTheme, setFontScale, isSpanish: language === "es" }),
    [language, theme, fontScale],
  );

  return <DemoPreferencesContext.Provider value={value}>{children}</DemoPreferencesContext.Provider>;
}

export function useDemoPreferences() {
  const context = useContext(DemoPreferencesContext);
  if (!context) throw new Error("useDemoPreferences must be used within DemoPreferencesProvider");
  return context;
}
