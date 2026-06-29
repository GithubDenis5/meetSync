import React, { useState } from "react";
import {
  Box, CssBaseline, Drawer, IconButton, List, ListItem,
  ListItemButton, ListItemIcon, ListItemText, Toolbar, Typography,
  Badge, Avatar, Menu, MenuItem, Divider, Tooltip,
} from "@mui/material";
import {
  Menu as MenuIcon, Dashboard, Group, CalendarMonth, Lightbulb,
  HowToVote, Recommend, Settings, Notifications, Logout,
  Brightness4, Brightness7, ChevronLeft,
} from "@mui/icons-material";
import OnboardingDialog from "./OnboardingDialog";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useThemeMode } from "../context/ThemeContext";

const DRAWER_WIDTH = 260;
const DRAWER_COLLAPSED = 72;

const NAV_ITEMS = [
  { label: "Dashboard", icon: <Dashboard />, path: "/" },
  { label: "My Groups", icon: <Group />, path: "/groups" },
  { label: "Calendar", icon: <CalendarMonth />, path: "/calendar" },
  { label: "Bank of Ideas", icon: <Lightbulb />, path: "/ideas" },
  { label: "Voting", icon: <HowToVote />, path: "/voting" },
  { label: "Recommendations", icon: <Recommend />, path: "/recommendations" },
  { label: "Settings", icon: <Settings />, path: "/settings" },
];

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const { mode, toggle: toggleTheme } = useThemeMode();

  const currentPage = NAV_ITEMS.find((item) => item.path === location.pathname);

  const drawerContent = (
    <Box sx={{ display: "flex", flexDirection: "column", height: "100%" }}>
      {/* ─── Logo Area ─────────────────────────── */}
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: collapsed ? "center" : "space-between",
          px: collapsed ? 1 : 2.5,
          py: 2,
          minHeight: 64,
        }}
      >
        {!collapsed && (
          <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
            <Box
              sx={{
                width: 32,
                height: 32,
                borderRadius: 1.5,
                background: "linear-gradient(135deg, #6366f1 0%, #818cf8 100%)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "white",
                fontWeight: 700,
                fontSize: "0.875rem",
              }}
            >
              M
            </Box>
            <Typography
              variant="h6"
              sx={{ fontWeight: 700, fontSize: "1.125rem", letterSpacing: "-0.02em" }}
            >
              MeetSync
            </Typography>
          </Box>
        )}
        {collapsed && (
          <Box
            sx={{
              width: 32,
              height: 32,
              borderRadius: 1.5,
              background: "linear-gradient(135deg, #6366f1 0%, #818cf8 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "white",
              fontWeight: 700,
              fontSize: "0.875rem",
            }}
          >
            M
          </Box>
        )}
      </Box>

      <Divider sx={{ mx: collapsed ? 1 : 2 }} />

      {/* ─── Navigation ────────────────────────── */}
      <List sx={{ flex: 1, px: collapsed ? 0.5 : 1.5, py: 1.5 }}>
        {NAV_ITEMS.map((item) => {
          const selected = location.pathname === item.path ||
            (item.path !== "/" && location.pathname.startsWith(item.path));
          return (
            <ListItem key={item.path} disablePadding sx={{ mb: 0.5 }}>
              <Tooltip title={collapsed ? item.label : ""} placement="right" arrow>
                <ListItemButton
                  selected={selected}
                  onClick={() => {
                    navigate(item.path);
                    setMobileOpen(false);
                  }}
                  sx={{
                    borderRadius: 2,
                    minHeight: 44,
                    justifyContent: collapsed ? "center" : "initial",
                    px: collapsed ? 1 : 2,
                    py: 1,
                    position: "relative",
                    "&.Mui-selected": {
                      backgroundColor: "rgba(99, 102, 241, 0.1)",
                      "&::before": collapsed ? {} : {
                        content: '""',
                        position: "absolute",
                        left: -8,
                        top: "50%",
                        transform: "translateY(-50%)",
                        width: 3,
                        height: 20,
                        borderRadius: 2,
                        backgroundColor: "primary.main",
                      },
                      "&:hover": {
                        backgroundColor: "rgba(99, 102, 241, 0.14)",
                      },
                    },
                    "&:hover": {
                      backgroundColor: "action.hover",
                    },
                  }}
                >
                  <ListItemIcon
                    sx={{
                      minWidth: collapsed ? 0 : 40,
                      justifyContent: "center",
                      color: selected ? "primary.main" : "text.secondary",
                    }}
                  >
                    {item.icon}
                  </ListItemIcon>
                  {!collapsed && (
                    <ListItemText
                      primary={item.label}
                      primaryTypographyProps={{
                        fontSize: "0.875rem",
                        fontWeight: selected ? 600 : 400,
                        color: selected ? "primary.main" : "text.primary",
                      }}
                    />
                  )}
                </ListItemButton>
              </Tooltip>
            </ListItem>
          );
        })}
      </List>

      <Divider sx={{ mx: collapsed ? 1 : 2 }} />

      {/* ─── Collapse Toggle ───────────────────── */}
      <Box sx={{ px: collapsed ? 0.5 : 1.5, py: 1 }}>
        <ListItem disablePadding>
          <Tooltip title={collapsed ? "Expand sidebar" : "Collapse sidebar"} placement="right" arrow>
            <ListItemButton
              onClick={() => setCollapsed(!collapsed)}
              sx={{
                borderRadius: 2,
                minHeight: 44,
                justifyContent: collapsed ? "center" : "initial",
                px: collapsed ? 1 : 2,
              }}
            >
              <ListItemIcon
                sx={{
                  minWidth: collapsed ? 0 : 40,
                  justifyContent: "center",
                  color: "text.secondary",
                }}
              >
                <ChevronLeft sx={{ transform: collapsed ? "rotate(180deg)" : "none", transition: "transform 0.2s" }} />
              </ListItemIcon>
              {!collapsed && (
                <ListItemText
                  primary="Collapse"
                  primaryTypographyProps={{ fontSize: "0.8125rem", color: "text.secondary" }}
                />
              )}
            </ListItemButton>
          </Tooltip>
        </ListItem>
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: "flex", minHeight: "100vh" }}>
      <CssBaseline />
      <OnboardingDialog />

      {/* ─── Top App Bar ────────────────────────── */}
      <Box
        component="header"
        sx={{
          position: "fixed",
          top: 0,
          left: { md: collapsed ? DRAWER_COLLAPSED : DRAWER_WIDTH },
          right: 0,
          height: 56,
          zIndex: 1100,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          px: { xs: 2, sm: 3 },
          bgcolor: "background.default",
          borderBottom: 1,
          borderColor: "divider",
          transition: "left 0.2s ease",
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
          <IconButton
            color="inherit"
            edge="start"
            sx={{ display: { md: "none" }, mr: 0.5 }}
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            <MenuIcon />
          </IconButton>
          <Typography
            variant="h5"
            sx={{
              fontWeight: 700,
              fontSize: "1.125rem",
              letterSpacing: "-0.02em",
            }}
          >
            {currentPage?.label || "MeetSync"}
          </Typography>
        </Box>

        <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
          {/* Theme toggle */}
          <Tooltip title={mode === "dark" ? "Light mode" : "Dark mode"}>
            <IconButton onClick={toggleTheme} size="small" sx={{ color: "text.secondary" }}>
              {mode === "dark" ? <Brightness7 fontSize="small" /> : <Brightness4 fontSize="small" />}
            </IconButton>
          </Tooltip>

          {/* Notifications */}
          <IconButton
            color="inherit"
            onClick={() => navigate("/notifications")}
            size="small"
            sx={{ color: "text.secondary" }}
          >
            <Badge badgeContent={0} color="error" variant="dot">
              <Notifications fontSize="small" />
            </Badge>
          </IconButton>

          {/* Avatar */}
          <IconButton
            onClick={(e) => setAnchorEl(e.currentTarget)}
            size="small"
            sx={{ ml: 0.5 }}
          >
            <Avatar
              sx={{
                width: 32,
                height: 32,
                bgcolor: "primary.main",
                fontSize: "0.8125rem",
                fontWeight: 600,
              }}
            >
              {user?.name?.[0] || "U"}
            </Avatar>
          </IconButton>

          {/* Avatar Menu */}
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={() => setAnchorEl(null)}
            transformOrigin={{ horizontal: "right", vertical: "top" }}
            anchorOrigin={{ horizontal: "right", vertical: "bottom" }}
            PaperProps={{
              sx: {
                mt: 1,
                minWidth: 180,
                borderRadius: 2,
                boxShadow: "0 4px 16px rgba(0,0,0,0.12)",
              },
            }}
          >
            <Box sx={{ px: 2, py: 1 }}>
              <Typography variant="body2" fontWeight={600}>{user?.name}</Typography>
              <Typography variant="caption" color="text.secondary">{user?.email}</Typography>
            </Box>
            <Divider />
            <MenuItem onClick={() => { setAnchorEl(null); navigate("/settings"); }} sx={{ mx: 0.5, my: 0.25 }}>
              <ListItemIcon>
                <Settings fontSize="small" />
              </ListItemIcon>
              Settings
            </MenuItem>
            <MenuItem onClick={logout} sx={{ mx: 0.5, my: 0.25 }}>
              <ListItemIcon>
                <Logout fontSize="small" />
              </ListItemIcon>
              Logout
            </MenuItem>
          </Menu>
        </Box>
      </Box>

      {/* ─── Sidebar (Desktop) ──────────────────── */}
      <Box
        component="nav"
        sx={{
          width: { md: collapsed ? DRAWER_COLLAPSED : DRAWER_WIDTH },
          flexShrink: { md: 0 },
          display: { xs: "none", md: "block" },
          transition: "width 0.2s ease",
        }}
      >
        <Drawer
          variant="permanent"
          open
          PaperProps={{
            sx: {
              width: collapsed ? DRAWER_COLLAPSED : DRAWER_WIDTH,
              borderRight: 1,
              borderColor: "divider",
              bgcolor: "background.paper",
              transition: "width 0.2s ease",
              overflow: "hidden",
              "&::-webkit-scrollbar": { width: 0 },
            },
          }}
        >
          <Toolbar sx={{ minHeight: "56px !important" }} />
          {drawerContent}
        </Drawer>
      </Box>

      {/* ─── Sidebar (Mobile Drawer) ────────────── */}
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={() => setMobileOpen(false)}
        ModalProps={{ keepMounted: true }}
        sx={{
          display: { xs: "block", md: "none" },
          "& .MuiDrawer-paper": {
            width: DRAWER_WIDTH,
            bgcolor: "background.paper",
          },
        }}
      >
        <Toolbar sx={{ minHeight: "56px !important" }} />
        {drawerContent}
      </Drawer>

      {/* ─── Main Content ───────────────────────── */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          mt: "56px",
          minHeight: "calc(100vh - 56px)",
          width: { md: `calc(100% - ${collapsed ? DRAWER_COLLAPSED : DRAWER_WIDTH}px)` },
          transition: "width 0.2s ease",
        }}
      >
        <Box
          sx={{
            maxWidth: 1200,
            mx: "auto",
            p: { xs: 2, sm: 3, md: 4 },
          }}
        >
          {children}
        </Box>
      </Box>
    </Box>
  );
};

export default Layout;
