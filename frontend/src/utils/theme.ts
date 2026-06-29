import { createTheme, ThemeOptions } from "@mui/material/styles";

// ─── Design Tokens ──────────────────────────────────────────

const FONT_FAMILY = '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

const SPACING = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

const RADIUS = {
  sm: 6,
  md: 8,
  lg: 12,
  xl: 16,
  full: 9999,
};

const SHADOWS_LIGHT = {
  sm: "0 1px 2px 0 rgba(0,0,0,0.05)",
  md: "0 1px 3px 0 rgba(0,0,0,0.06), 0 1px 2px -1px rgba(0,0,0,0.06)",
  lg: "0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -2px rgba(0,0,0,0.05)",
  xl: "0 10px 15px -3px rgba(0,0,0,0.08), 0 4px 6px -4px rgba(0,0,0,0.04)",
};

const SHADOWS_DARK = {
  sm: "0 1px 2px 0 rgba(0,0,0,0.3)",
  md: "0 1px 3px 0 rgba(0,0,0,0.35), 0 1px 2px -1px rgba(0,0,0,0.3)",
  lg: "0 4px 6px -1px rgba(0,0,0,0.4), 0 2px 4px -2px rgba(0,0,0,0.35)",
  xl: "0 10px 15px -3px rgba(0,0,0,0.45), 0 4px 6px -4px rgba(0,0,0,0.35)",
};

// ─── Color Primitives ───────────────────────────────────────

const colors = {
  // Primary: Warm indigo-purple
  primary: {
    50: "#eef2ff",
    100: "#e0e7ff",
    200: "#c7d2fe",
    300: "#a5b4fc",
    400: "#818cf8",
    500: "#6366f1",
    600: "#4f46e5",
    700: "#4338ca",
    800: "#3730a3",
    900: "#312e81",
  },
  // Neutral warm grays
  neutral: {
    50: "#f8f9fa",
    100: "#f1f3f5",
    200: "#e9ecef",
    300: "#dee2e6",
    400: "#ced4da",
    500: "#adb5bd",
    600: "#6c757d",
    700: "#495057",
    800: "#343a40",
    900: "#212529",
    950: "#1a1b1e",
  },
  success: {
    50: "#f0fdf4",
    100: "#dcfce7",
    200: "#bbf7d0",
    300: "#86efac",
    400: "#4ade80",
    500: "#22c55e",
    600: "#16a34a",
    700: "#15803d",
  },
  warning: {
    50: "#fffbeb",
    100: "#fef3c7",
    200: "#fde68a",
    300: "#fcd34d",
    400: "#fbbf24",
    500: "#f59e0b",
    600: "#d97706",
    700: "#b45309",
  },
  error: {
    50: "#fef2f2",
    100: "#fee2e2",
    200: "#fecaca",
    300: "#fca5a5",
    400: "#f87171",
    500: "#ef4444",
    600: "#dc2626",
    700: "#b91c1c",
  },
};

// ─── Light Theme ────────────────────────────────────────────

const lightTheme: ThemeOptions = {
  palette: {
    mode: "light",
    primary: {
      main: colors.primary[500],
      light: colors.primary[400],
      dark: colors.primary[600],
      contrastText: "#ffffff",
    },
    secondary: {
      main: colors.primary[400],
      light: colors.primary[300],
      dark: colors.primary[500],
      contrastText: "#ffffff",
    },
    success: {
      main: colors.success[500],
      light: colors.success[400],
      dark: colors.success[600],
    },
    warning: {
      main: colors.warning[500],
      light: colors.warning[400],
      dark: colors.warning[600],
    },
    error: {
      main: colors.error[500],
      light: colors.error[400],
      dark: colors.error[600],
    },
    background: {
      default: colors.neutral[50],
      paper: "#ffffff",
    },
    text: {
      primary: colors.neutral[950],
      secondary: colors.neutral[600],
      disabled: colors.neutral[400],
    },
    divider: colors.neutral[200],
    action: {
      active: colors.primary[500],
      hover: "rgba(99, 102, 241, 0.08)",
      selected: "rgba(99, 102, 241, 0.12)",
      disabled: colors.neutral[300],
      disabledBackground: colors.neutral[100],
    },
  },
  typography: {
    fontFamily: FONT_FAMILY,
    h1: { fontWeight: 800, fontSize: "2.5rem", lineHeight: 1.2, letterSpacing: "-0.03em" },
    h2: { fontWeight: 700, fontSize: "2rem", lineHeight: 1.25, letterSpacing: "-0.02em" },
    h3: { fontWeight: 700, fontSize: "1.5rem", lineHeight: 1.3, letterSpacing: "-0.02em" },
    h4: { fontWeight: 700, fontSize: "1.25rem", lineHeight: 1.35, letterSpacing: "-0.015em" },
    h5: { fontWeight: 600, fontSize: "1.125rem", lineHeight: 1.4, letterSpacing: "-0.01em" },
    h6: { fontWeight: 600, fontSize: "1rem", lineHeight: 1.5, letterSpacing: "-0.005em" },
    subtitle1: { fontWeight: 500, fontSize: "0.9375rem", lineHeight: 1.5 },
    subtitle2: { fontWeight: 500, fontSize: "0.8125rem", lineHeight: 1.5, letterSpacing: "0.01em", color: colors.neutral[600] },
    body1: { fontWeight: 400, fontSize: "0.9375rem", lineHeight: 1.6 },
    body2: { fontWeight: 400, fontSize: "0.8125rem", lineHeight: 1.6 },
    caption: { fontWeight: 400, fontSize: "0.75rem", lineHeight: 1.5, color: colors.neutral[500] },
    button: { fontWeight: 500, fontSize: "0.875rem", lineHeight: 1.5, textTransform: "none" as const },
    overline: { fontWeight: 600, fontSize: "0.6875rem", lineHeight: 1.5, letterSpacing: "0.08em", textTransform: "uppercase" as const },
  },
  shape: { borderRadius: RADIUS.md },
  spacing: 8,
};

// ─── Dark Theme ─────────────────────────────────────────────

const darkTheme: ThemeOptions = {
  ...lightTheme,
  palette: {
    mode: "dark",
    primary: {
      main: colors.primary[400],
      light: colors.primary[300],
      dark: colors.primary[500],
      contrastText: "#0f1117",
    },
    secondary: {
      main: colors.primary[300],
      light: colors.primary[200],
      dark: colors.primary[400],
      contrastText: "#0f1117",
    },
    success: {
      main: colors.success[400],
      light: colors.success[300],
      dark: colors.success[500],
    },
    warning: {
      main: colors.warning[400],
      light: colors.warning[300],
      dark: colors.warning[500],
    },
    error: {
      main: colors.error[400],
      light: colors.error[300],
      dark: colors.error[500],
    },
    background: {
      default: "#0f1117",
      paper: "#1a1c23",
    },
    text: {
      primary: "#f1f3f5",
      secondary: colors.neutral[400],
      disabled: colors.neutral[600],
    },
    divider: "#2e3039",
    action: {
      active: colors.primary[400],
      hover: "rgba(129, 140, 248, 0.12)",
      selected: "rgba(129, 140, 248, 0.2)",
      disabled: colors.neutral[600],
      disabledBackground: "rgba(255,255,255,0.05)",
    },
  },
};

// ─── Shared Component Overrides ─────────────────────────────

const components: ThemeOptions["components"] = {
  MuiCssBaseline: {
    styleOverrides: {
      body: {
        WebkitFontSmoothing: "antialiased",
        MozOsxFontSmoothing: "grayscale",
      },
    },
  },
  MuiButton: {
    defaultProps: {
      disableElevation: true,
    },
    styleOverrides: {
      root: {
        borderRadius: RADIUS.sm,
        padding: "8px 16px",
        fontWeight: 500,
        fontSize: "0.875rem",
        lineHeight: 1.5,
        transition: "all 0.15s ease",
        "&:active": {
          transform: "scale(0.97)",
        },
      },
      sizeSmall: {
        padding: "5px 12px",
        fontSize: "0.8125rem",
      },
      sizeLarge: {
        padding: "12px 24px",
        fontSize: "0.9375rem",
      },
      contained: {
        boxShadow: SHADOWS_LIGHT.sm,
        "&:hover": {
          boxShadow: SHADOWS_LIGHT.md,
        },
      },
      outlined: {
        borderWidth: "1.5px",
        "&:hover": {
          borderWidth: "1.5px",
        },
      },
    },
  },
  MuiCard: {
    styleOverrides: {
      root: {
        borderRadius: RADIUS.lg,
        boxShadow: SHADOWS_LIGHT.md,
        backgroundImage: "none",
        transition: "box-shadow 0.2s ease, transform 0.15s ease",
        "&:hover": {
          boxShadow: SHADOWS_LIGHT.lg,
        },
      },
    },
  },
  MuiCardContent: {
    styleOverrides: {
      root: {
        padding: 24,
        "&:last-child": {
          paddingBottom: 24,
        },
      },
    },
  },
  MuiDialog: {
    styleOverrides: {
      paper: {
        borderRadius: RADIUS.xl,
        boxShadow: SHADOWS_LIGHT.xl,
        backgroundImage: "none",
      },
    },
  },
  MuiDialogTitle: {
    styleOverrides: {
      root: {
        fontSize: "1.125rem",
        fontWeight: 600,
        padding: "24px 24px 8px",
      },
    },
  },
  MuiDialogContent: {
    styleOverrides: {
      root: {
        padding: "8px 24px 24px",
      },
    },
  },
  MuiDialogActions: {
    styleOverrides: {
      root: {
        padding: "8px 24px 24px",
        gap: 8,
      },
    },
  },
  MuiChip: {
    styleOverrides: {
      root: {
        borderRadius: RADIUS.sm,
        fontWeight: 500,
        fontSize: "0.75rem",
        height: 28,
      },
      sizeSmall: {
        height: 22,
        fontSize: "0.6875rem",
      },
      outlined: {
        borderWidth: "1.5px",
      },
    },
  },
  MuiTextField: {
    defaultProps: {
      variant: "outlined",
    },
    styleOverrides: {
      root: {
        "& .MuiOutlinedInput-root": {
          borderRadius: RADIUS.sm,
          transition: "box-shadow 0.15s ease",
          "&.Mui-focused": {
            boxShadow: `0 0 0 3px ${colors.primary[100]}`,
          },
        },
      },
    },
  },
  MuiSelect: {
    defaultProps: {
      variant: "outlined",
    },
    styleOverrides: {
      root: {
        borderRadius: RADIUS.sm,
      },
    },
  },
  MuiTabs: {
    styleOverrides: {
      root: {
        minHeight: 40,
      },
      indicator: {
        height: 2.5,
        borderRadius: 2,
      },
    },
  },
  MuiTab: {
    styleOverrides: {
      root: {
        textTransform: "none",
        fontWeight: 500,
        fontSize: "0.875rem",
        minHeight: 40,
        padding: "8px 16px",
        borderRadius: `${RADIUS.sm}px ${RADIUS.sm}px 0 0`,
        "&.Mui-selected": {
          fontWeight: 600,
        },
      },
    },
  },
  MuiToggleButton: {
    styleOverrides: {
      root: {
        borderRadius: RADIUS.sm,
        borderWidth: "1.5px",
        textTransform: "none",
        fontWeight: 500,
        "&.Mui-selected": {
          borderWidth: "1.5px",
        },
      },
    },
  },
  MuiToggleButtonGroup: {
    styleOverrides: {
      root: {
        borderRadius: RADIUS.sm,
        gap: 0,
      },
    },
  },
  MuiMenuItem: {
    styleOverrides: {
      root: {
        borderRadius: RADIUS.sm,
        margin: "2px 6px",
        padding: "8px 12px",
        fontSize: "0.875rem",
        "&:hover": {
          backgroundColor: colors.neutral[100],
        },
      },
    },
  },
  MuiList: {
    styleOverrides: {
      root: {
        padding: 4,
      },
    },
  },
  MuiListItem: {
    styleOverrides: {
      root: {
        borderRadius: RADIUS.sm,
      },
    },
  },
  MuiListItemButton: {
    styleOverrides: {
      root: {
        borderRadius: RADIUS.sm,
        margin: "1px 0",
        transition: "all 0.12s ease",
      },
    },
  },
  MuiTooltip: {
    styleOverrides: {
      tooltip: {
        borderRadius: RADIUS.sm,
        padding: "6px 10px",
        fontSize: "0.75rem",
        fontWeight: 500,
        backgroundColor: colors.neutral[900],
      },
    },
  },
  MuiAlert: {
    styleOverrides: {
      root: {
        borderRadius: RADIUS.md,
        padding: "10px 16px",
        fontSize: "0.875rem",
      },
      standardSuccess: {
        backgroundColor: colors.success[50],
        color: colors.success[700],
      },
      standardError: {
        backgroundColor: colors.error[50],
        color: colors.error[700],
      },
      standardWarning: {
        backgroundColor: colors.warning[50],
        color: colors.warning[700],
      },
      standardInfo: {
        backgroundColor: colors.primary[50],
        color: colors.primary[900],
      },
    },
  },
  MuiSnackbarContent: {
    styleOverrides: {
      root: {
        borderRadius: RADIUS.md,
      },
    },
  },
  MuiAvatar: {
    styleOverrides: {
      root: {
        borderRadius: RADIUS.sm,
        fontWeight: 600,
        fontSize: "0.875rem",
      },
    },
  },
  MuiBadge: {
    styleOverrides: {
      badge: {
        fontSize: "0.625rem",
        minWidth: 16,
        height: 16,
        fontWeight: 600,
      },
    },
  },
  MuiPaper: {
    styleOverrides: {
      root: {
        backgroundImage: "none",
      },
    },
  },
  MuiTable: {
    styleOverrides: {
      root: {
        borderRadius: RADIUS.md,
      },
    },
  },
  MuiTableRow: {
    styleOverrides: {
      root: {
        transition: "background-color 0.12s ease",
        "&:hover": {
          backgroundColor: colors.neutral[50],
        },
      },
    },
  },
};

// ─── Build Themes ───────────────────────────────────────────

export const light = createTheme({
  ...lightTheme,
  components: {
    ...components,
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: "rgba(255,255,255,0.8)",
          backdropFilter: "blur(12px)",
          boxShadow: "none",
          borderBottom: `1px solid ${colors.neutral[200]}`,
          backgroundImage: "none",
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          borderRight: `1px solid ${colors.neutral[200]}`,
          backgroundColor: "#ffffff",
          backgroundImage: "none",
        },
      },
    },
    MuiCard: {
      ...components!.MuiCard!,
      styleOverrides: {
        root: {
          borderRadius: RADIUS.lg,
          boxShadow: SHADOWS_LIGHT.md,
          backgroundImage: "none",
          transition: "box-shadow 0.2s ease, transform 0.15s ease",
          "&:hover": {
            boxShadow: SHADOWS_LIGHT.lg,
          },
        },
      },
    },
    MuiTextField: {
      ...components!.MuiTextField!,
      styleOverrides: {
        root: {
          "& .MuiOutlinedInput-root": {
            borderRadius: RADIUS.sm,
            transition: "box-shadow 0.15s ease",
            backgroundColor: "#ffffff",
            "&.Mui-focused": {
              boxShadow: `0 0 0 3px ${colors.primary[100]}`,
            },
          },
        },
      },
    },
  },
});

export const dark = createTheme({
  ...darkTheme,
  components: {
    ...components,
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: "rgba(15,17,23,0.8)",
          backdropFilter: "blur(12px)",
          boxShadow: "none",
          borderBottom: `1px solid #2e3039`,
          backgroundImage: "none",
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          borderRight: `1px solid #2e3039`,
          backgroundColor: "#1a1c23",
          backgroundImage: "none",
        },
      },
    },
    MuiCard: {
      ...components!.MuiCard!,
      styleOverrides: {
        root: {
          borderRadius: RADIUS.lg,
          boxShadow: SHADOWS_DARK.md,
          backgroundImage: "none",
          transition: "box-shadow 0.2s ease, transform 0.15s ease",
          "&:hover": {
            boxShadow: SHADOWS_DARK.lg,
          },
        },
      },
    },
    MuiTextField: {
      ...components!.MuiTextField!,
      styleOverrides: {
        root: {
          "& .MuiOutlinedInput-root": {
            borderRadius: RADIUS.sm,
            transition: "box-shadow 0.15s ease",
            backgroundColor: "#0f1117",
            "&.Mui-focused": {
              boxShadow: `0 0 0 3px rgba(129, 140, 248, 0.25)`,
            },
          },
        },
      },
    },
    MuiMenuItem: {
      ...components!.MuiMenuItem!,
      styleOverrides: {
        root: {
          borderRadius: RADIUS.sm,
          margin: "2px 6px",
          padding: "8px 12px",
          fontSize: "0.875rem",
          "&:hover": {
            backgroundColor: "rgba(255,255,255,0.06)",
          },
        },
      },
    },
    MuiTableRow: {
      ...components!.MuiTableRow!,
      styleOverrides: {
        root: {
          transition: "background-color 0.12s ease",
          "&:hover": {
            backgroundColor: "rgba(255,255,255,0.04)",
          },
        },
      },
    },
    MuiAlert: {
      ...components!.MuiAlert!,
      styleOverrides: {
        root: {
          borderRadius: RADIUS.md,
          padding: "10px 16px",
          fontSize: "0.875rem",
        },
        standardSuccess: {
          backgroundColor: "rgba(34,197,94,0.12)",
          color: colors.success[300],
        },
        standardError: {
          backgroundColor: "rgba(239,68,68,0.12)",
          color: colors.error[300],
        },
        standardWarning: {
          backgroundColor: "rgba(245,158,11,0.12)",
          color: colors.warning[300],
        },
        standardInfo: {
          backgroundColor: "rgba(129,140,248,0.12)",
          color: colors.primary[300],
        },
      },
    },
  },
});
