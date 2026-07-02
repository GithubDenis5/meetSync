import React, { useState, useEffect, useCallback } from "react";
import {
  Box, Typography, Card, CardContent, Grid, Chip, Button,
  Select, MenuItem, FormControl, InputLabel, CircularProgress,
  ToggleButtonGroup, ToggleButton, Dialog, DialogTitle,
  DialogContent, DialogActions, TextField, Tooltip, AvatarGroup,
  Avatar, IconButton, Badge, Snackbar, Alert, useMediaQuery,
  Drawer,
} from "@mui/material";
import { Add, ArrowBack, ArrowForward, Event, Delete, Schedule } from "@mui/icons-material";
import { groupApi, calendarApi, meetingApi } from "../utils/api";
import { Group, Meeting, RsvpStatus, RecurringRule } from "../types";

const STATUS_COLORS: Record<string, string> = {
  free: "#4caf50",
  busy: "#f44336",
  maybe: "#ff9800",
  unknown: "#9e9e9e",
};

const RSVP_LABELS: Record<RsvpStatus, string> = {
  going: "Going",
  not_going: "Not Going",
  maybe: "Maybe",
};

const CalendarPage: React.FC = () => {
  const [groups, setGroups] = useState<Group[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<number | "">("");
  const [availabilities, setAvailabilities] = useState<Record<string, { status: string }>>({});
  const [groupAvailabilities, setGroupAvailabilities] = useState<Record<string, { user_id: number; name: string; status: string }[]>>({});
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [loading, setLoading] = useState(true);
  const [month, setMonth] = useState(new Date().getMonth());
  const [year, setYear] = useState(new Date().getFullYear());
  const isMobile = useMediaQuery("(max-width:600px)");

  // Meeting dialog
  const [meetingDialogOpen, setMeetingDialogOpen] = useState(false);
  const [selectedMeeting, setSelectedMeeting] = useState<Meeting | null>(null);
  const [rsvpStatus, setRsvpStatus] = useState<RsvpStatus | null>(null);
  const [rsvpLoading, setRsvpLoading] = useState(false);

  // Create meeting dialog
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newMeeting, setNewMeeting] = useState({
    title: "",
    description: "",
    time: "",
    location: "",
  });
  const [createDate, setCreateDate] = useState("");

  // Mobile day detail
  const [selectedDay, setSelectedDay] = useState<number | null>(null);
  const [dayDetailOpen, setDayDetailOpen] = useState(false);

  // Drag-to-select
  const [dragActive, setDragActive] = useState(false);
  const [dragStatus, setDragStatus] = useState<string | null>(null);
  const [pendingChanges, setPendingChanges] = useState<Record<string, string>>({});

  // Recurring rules (weekly pattern)
  const [recurringRules, setRecurringRules] = useState<RecurringRule[]>([]);
  const [weeklyPatternOpen, setWeeklyPatternOpen] = useState(false);
  const [patternStatus, setPatternStatus] = useState<string>("free");
  const [patternStartTime, setPatternStartTime] = useState("");
  const [patternEndTime, setPatternEndTime] = useState("");

  // Snackbar
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: "success" | "error" }>({
    open: false, message: "", severity: "success",
  });

  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const firstDay = new Date(year, month, 1).getDay();
  const days = Array.from({ length: daysInMonth }, (_, i) => i + 1);

  // Load groups
  useEffect(() => {
    groupApi.list().then(({ data }) => {
      setGroups(data);
      if (data.length > 0) setSelectedGroup(data[0].id);
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  // Load availability, recurring rules, and meetings when group/month changes
  const loadData = useCallback(() => {
    if (!selectedGroup) return;
    const startDate = `${year}-${String(month + 1).padStart(2, "0")}-01`;
    const endDate = new Date(year, month + 1, 0).toISOString().split("T")[0];

    // Personal availability
    calendarApi.getMyAvailability(Number(selectedGroup), startDate, endDate)
      .then(({ data }) => {
        const map: Record<string, { status: string }> = {};
        data.forEach((a: { date: string; status: string }) => { map[a.date] = { status: a.status }; });
        setAvailabilities(map);
      }).catch(() => {});

    // Group calendar (who's free/busy)
    calendarApi.getGroupCalendar(Number(selectedGroup), startDate, endDate)
      .then(({ data }) => {
        const map: Record<string, { user_id: number; name: string; status: string }[]> = {};
        data.forEach((a: { date: string; user_id: number; user_name?: string; name?: string; status: string }) => {
          if (!map[a.date]) map[a.date] = [];
          map[a.date].push({ user_id: a.user_id, name: a.user_name || a.name || "Unknown", status: a.status });
        });
        setGroupAvailabilities(map);
      }).catch(() => {});

    // Recurring rules
    calendarApi.listRecurringRules(Number(selectedGroup))
      .then(({ data }) => setRecurringRules(data))
      .catch(() => setRecurringRules([]));

    // Meetings
    meetingApi.list(Number(selectedGroup))
      .then(({ data }) => setMeetings(Array.isArray(data) ? data : []))
      .catch(() => setMeetings([]));
  }, [selectedGroup, month, year]);

  useEffect(() => { loadData(); }, [loadData]);

  // ─── Drag-to-select ───────────────────────────────────────────

  const handleDragStart = (day: number, status: string) => {
    if (isMobile) return;
    setDragActive(true);
    setDragStatus(status);
    const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    setAvailabilities((prev) => ({ ...prev, [dateStr]: { status } }));
    setPendingChanges((prev) => ({ ...prev, [dateStr]: status }));
  };

  const handleDragEnter = (day: number) => {
    if (!dragActive || !dragStatus || isMobile) return;
    const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    setAvailabilities((prev) => ({ ...prev, [dateStr]: { status: dragStatus } }));
    setPendingChanges((prev) => ({ ...prev, [dateStr]: dragStatus! }));
  };

  const handleDragEnd = async () => {
    if (!dragActive || !selectedGroup) {
      setDragActive(false);
      setDragStatus(null);
      return;
    }
    setDragActive(false);
    setDragStatus(null);

    // Batch-commit all pending changes
    const entries = Object.entries(pendingChanges);
    if (entries.length > 0) {
      const batch = entries.map(([date, status]) => ({
        group_id: Number(selectedGroup),
        date,
        status,
      }));
      try {
        await calendarApi.setAvailabilityBatch(Number(selectedGroup), batch);
        // Refresh group calendar
        const startDate = `${year}-${String(month + 1).padStart(2, "0")}-01`;
        const endDate = new Date(year, month + 1, 0).toISOString().split("T")[0];
        calendarApi.getGroupCalendar(Number(selectedGroup), startDate, endDate)
          .then(({ data }) => {
            const map: Record<string, { user_id: number; name: string; status: string }[]> = {};
            data.forEach((a: { date: string; user_id: number; user_name?: string; name?: string; status: string }) => {
              if (!map[a.date]) map[a.date] = [];
              map[a.date].push({ user_id: a.user_id, name: a.user_name || a.name || "Unknown", status: a.status });
            });
            setGroupAvailabilities(map);
          }).catch(() => {});
      } catch {
        // Revert on failure
        loadData();
      }
    }
    setPendingChanges({});
  };

  // Quick week actions
  const applyWeekPattern = async (status: string) => {
    if (!selectedGroup) return;
    const startDate = `${year}-${String(month + 1).padStart(2, "0")}-01`;
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const batch = [];
    for (let d = 1; d <= daysInMonth; d++) {
      const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
      batch.push({ group_id: Number(selectedGroup), date: dateStr, status });
    }
    try {
      await calendarApi.setAvailabilityBatch(Number(selectedGroup), batch);
      setSnackbar({ open: true, message: `Marked ${daysInMonth} days as "${status}"`, severity: "success" });
      loadData();
    } catch {
      setSnackbar({ open: true, message: "Failed to update", severity: "error" });
    }
  };

  const updateStatus = async (day: number, status: string) => {
    if (!selectedGroup) return;
    const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    try {
      await calendarApi.setAvailability({ group_id: Number(selectedGroup), date: dateStr, status });
      setAvailabilities((prev) => ({
        ...prev,
        [dateStr]: { status },
      }));
      // Re-fetch group availability to reflect the change
      const startDate = `${year}-${String(month + 1).padStart(2, "0")}-01`;
      const endDate = new Date(year, month + 1, 0).toISOString().split("T")[0];
      calendarApi.getGroupCalendar(Number(selectedGroup), startDate, endDate)
        .then(({ data }) => {
          const map: Record<string, { user_id: number; name: string; status: string }[]> = {};
          data.forEach((a: { date: string; user_id: number; user_name?: string; name?: string; status: string }) => {
            if (!map[a.date]) map[a.date] = [];
            map[a.date].push({ user_id: a.user_id, name: a.user_name || a.name || "Unknown", status: a.status });
          });
          setGroupAvailabilities(map);
        }).catch(() => {});
    } catch {
      setSnackbar({ open: true, message: "Failed to update availability", severity: "error" });
    }
  };

  const getStatus = (day: number) => {
    const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    return availabilities[dateStr]?.status || "unknown";
  };

  const getMeetingsForDay = (day: number) => {
    const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    return meetings.filter((m) => m.date === dateStr);
  };

  const getGroupStatusForDay = (day: number) => {
    const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    return groupAvailabilities[dateStr] || [];
  };

  const handleDayClick = (day: number) => {
    if (!isMobile) return;
    setSelectedDay(day);
    setDayDetailOpen(true);
  };

  const handleMeetingClick = (meeting: Meeting) => {
    setSelectedMeeting(meeting);
    setMeetingDialogOpen(true);
    setRsvpStatus(null);
  };

  const handleRsvp = async (status: RsvpStatus, meetingId?: number) => {
    const mId = meetingId || selectedMeeting?.id;
    if (!mId) return;
    setRsvpLoading(true);
    try {
      await meetingApi.rsvp(mId, status);
      setRsvpStatus(status);
      setSnackbar({ open: true, message: `RSVP: ${RSVP_LABELS[status]}`, severity: "success" });
      // Refresh meetings
      if (selectedGroup) {
        const { data } = await meetingApi.list(Number(selectedGroup));
        setMeetings(Array.isArray(data) ? data : []);
      }
    } catch {
      setSnackbar({ open: true, message: "Failed to RSVP", severity: "error" });
    } finally {
      setRsvpLoading(false);
    }
  };

  const findMyRsvp = (meeting: Meeting): RsvpStatus | undefined => {
    const currentUserId = localStorage.getItem("user_id");
    return meeting.participants?.find(
      (p) => String(p.user_id) === currentUserId
    )?.status as RsvpStatus | undefined;
  };

  const handleCreateMeeting = async () => {
    if (!selectedGroup || !createDate || !newMeeting.title.trim()) {
      setSnackbar({ open: true, message: "Title and date are required", severity: "error" });
      return;
    }
    try {
      await meetingApi.create({
        group_id: Number(selectedGroup),
        title: newMeeting.title,
        description: newMeeting.description,
        date: createDate,
        time: newMeeting.time || undefined,
        location: newMeeting.location || undefined,
      });
      setSnackbar({ open: true, message: "Event proposed!", severity: "success" });
      setCreateDialogOpen(false);
      setNewMeeting({ title: "", description: "", time: "", location: "" });
      setCreateDate("");
      // Refresh meetings
      const { data } = await meetingApi.list(Number(selectedGroup));
      setMeetings(Array.isArray(data) ? data : []);
    } catch {
      setSnackbar({ open: true, message: "Failed to create event", severity: "error" });
    }
  };

  const handleDeleteMeeting = async (meetingId: number) => {
    try {
      await meetingApi.delete(meetingId);
      setSnackbar({ open: true, message: "Event deleted", severity: "success" });
      setMeetingDialogOpen(false);
      setSelectedMeeting(null);
      if (selectedGroup) {
        const { data } = await meetingApi.list(Number(selectedGroup));
        setMeetings(Array.isArray(data) ? data : []);
      }
    } catch {
      setSnackbar({ open: true, message: "Failed to delete event", severity: "error" });
    }
  };

  const getParticipantCounts = (meeting: Meeting) => {
    const counts = { going: 0, not_going: 0, maybe: 0 };
    meeting.participants?.forEach((p) => {
      if (p.status in counts) counts[p.status as keyof typeof counts]++;
    });
    return counts;
  };

  // ─── Recurring Rules ──────────────────────────────────────────

  const DAYS_OF_WEEK = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"];

  const hasDayRule = (day: string) => recurringRules.some((r) => r.day_of_week === day);

  const toggleDayRule = async (day: string) => {
    if (!selectedGroup) return;
    const existing = recurringRules.find((r) => r.day_of_week === day);
    try {
      if (existing) {
        await calendarApi.deleteRecurringRule(existing.id);
        setRecurringRules((prev) => prev.filter((r) => r.id !== existing.id));
      } else {
        const { data } = await calendarApi.createRecurringRule({
          group_id: Number(selectedGroup),
          day_of_week: day,
          status: patternStatus,
          start_time: patternStartTime || undefined,
          end_time: patternEndTime || undefined,
        });
        setRecurringRules((prev) => [...prev, data]);
      }
      setSnackbar({ open: true, message: existing ? "Rule removed" : "Rule added", severity: "success" });
    } catch {
      setSnackbar({ open: true, message: "Failed to update rule", severity: "error" });
    }
  };

  const applyQuickPattern = async (days: string[], status: string) => {
    if (!selectedGroup) return;
    const startTime = status === "free" ? "09:00" : "";
    const endTime = status === "free" ? "18:00" : "";
    try {
      // Delete all existing rules first
      for (const rule of recurringRules) {
        await calendarApi.deleteRecurringRule(rule.id);
      }
      // Create new rules
      const newRules: RecurringRule[] = [];
      for (const day of days) {
        const { data } = await calendarApi.createRecurringRule({
          group_id: Number(selectedGroup),
          day_of_week: day,
          status,
          start_time: startTime || undefined,
          end_time: endTime || undefined,
        });
        newRules.push(data);
      }
      setRecurringRules(newRules);
      setSnackbar({ open: true, message: `Pattern applied (${days.length} days)`, severity: "success" });
    } catch {
      setSnackbar({ open: true, message: "Failed to apply pattern", severity: "error" });
    }
  };

  const clearAllRules = async () => {
    if (!selectedGroup) return;
    try {
      for (const rule of recurringRules) {
        await calendarApi.deleteRecurringRule(rule.id);
      }
      setRecurringRules([]);
      setSnackbar({ open: true, message: "All rules cleared", severity: "success" });
    } catch {
      setSnackbar({ open: true, message: "Failed to clear rules", severity: "error" });
    }
  };

  const prevMonth = () => {
    if (month === 0) { setMonth(11); setYear((prev) => prev - 1); }
    else setMonth((m) => m - 1);
  };

  const nextMonth = () => {
    if (month === 11) { setMonth(0); setYear((prev) => prev + 1); }
    else setMonth((m) => m + 1);
  };

  if (loading) return <Box sx={{ display: "flex", justifyContent: "center", mt: 4 }}><CircularProgress /></Box>;

  return (
    <>
      {/* ─── Header ───────────────────────────────────────────── */}
      <Box sx={{ display: "flex", flexDirection: { xs: "column", sm: "row" }, justifyContent: "space-between", alignItems: { xs: "stretch", sm: "center" }, mb: 2, gap: 1 }}>
        <Typography variant="h4" sx={{ fontSize: { xs: "1.5rem", sm: "2rem" } }}>Calendar</Typography>
        <Box sx={{ display: "flex", gap: 1, alignItems: "center", flexWrap: "wrap" }}>
          <FormControl size="small" sx={{ minWidth: { xs: 140, sm: 200 }, flex: { xs: 1, sm: "none" } }}>
            <InputLabel>Group</InputLabel>
            <Select value={selectedGroup} onChange={(e) => setSelectedGroup(e.target.value as number)} label="Group">
              {groups.map((g) => <MenuItem key={g.id} value={g.id}>{g.name}</MenuItem>)}
            </Select>
          </FormControl>
          <Button variant="contained" startIcon={<Add />} size="small" onClick={() => setCreateDialogOpen(true)}>
            Propose
          </Button>
        </Box>
      </Box>

      {/* ─── Month Navigation ──────────────────────────────────── */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
            <IconButton onClick={prevMonth}><ArrowBack /></IconButton>
            <Typography variant="h6">
              {new Date(year, month).toLocaleString("default", { month: "long", year: "numeric" })}
            </Typography>
            <IconButton onClick={nextMonth}><ArrowForward /></IconButton>
          </Box>

          {/* ─── Weekly Pattern (collapsible) ──────────────────── */}
          <Box sx={{ mb: 1.5 }}>
            <Button
              size="small"
              startIcon={<Schedule />}
              onClick={() => setWeeklyPatternOpen(!weeklyPatternOpen)}
              sx={{ textTransform: "none", fontSize: "0.8125rem" }}
            >
              {weeklyPatternOpen ? "Hide" : "Show"} Weekly Pattern
              {recurringRules.length > 0 && (
                <Chip label={`${recurringRules.length} day${recurringRules.length > 1 ? "s" : ""}`} size="small"
                  sx={{ ml: 1, height: 20, fontSize: 11, bgcolor: "primary.main", color: "white" }} />
              )}
            </Button>

            {weeklyPatternOpen && (
              <Box sx={{ mt: 1.5, p: 2, bgcolor: "action.hover", borderRadius: 2 }}>
                <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600, fontSize: "0.8125rem", color: "text.secondary" }}>
                  Set your typical weekly availability
                </Typography>

                {/* Day toggles */}
                <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap", mb: 1.5 }}>
                  {DAYS_OF_WEEK.map((day) => {
                    const active = hasDayRule(day);
                    const label = day.charAt(0).toUpperCase() + day.slice(1, 3);
                    return (
                      <Button
                        key={day}
                        size="small"
                        variant={active ? "contained" : "outlined"}
                        onClick={() => toggleDayRule(day)}
                        sx={{
                          minWidth: 40, fontSize: "0.7rem", py: 0.5,
                          bgcolor: active ? "primary.main" : undefined,
                          "&:hover": { bgcolor: active ? "primary.dark" : "action.hover" },
                        }}
                      >
                        {label}
                      </Button>
                    );
                  })}
                </Box>

                {/* Status + time */}
                <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", alignItems: "center", mb: 1.5 }}>
                  <FormControl size="small" sx={{ minWidth: 90 }}>
                    <InputLabel>Status</InputLabel>
                    <Select value={patternStatus} onChange={(e) => setPatternStatus(e.target.value)} label="Status">
                      <MenuItem value="free">Free</MenuItem>
                      <MenuItem value="busy">Busy</MenuItem>
                      <MenuItem value="maybe">Maybe</MenuItem>
                    </Select>
                  </FormControl>
                  <TextField size="small" type="time" label="From" value={patternStartTime}
                    onChange={(e) => setPatternStartTime(e.target.value)} InputLabelProps={{ shrink: true }}
                    sx={{ maxWidth: 120 }} />
                  <TextField size="small" type="time" label="To" value={patternEndTime}
                    onChange={(e) => setPatternEndTime(e.target.value)} InputLabelProps={{ shrink: true }}
                    sx={{ maxWidth: 120 }} />
                </Box>

                {/* Quick actions */}
                <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap" }}>
                  <Button size="small" variant="outlined" onClick={() =>
                    applyQuickPattern(["monday", "tuesday", "wednesday", "thursday", "friday"], "free")}>
                    Free weekdays
                  </Button>
                  <Button size="small" variant="outlined" onClick={() =>
                    applyQuickPattern(["saturday", "sunday"], "busy")}>
                    Busy weekends
                  </Button>
                  <Button size="small" variant="outlined" color="error" onClick={clearAllRules}>
                    Clear all
                  </Button>
                </Box>
              </Box>
            )}
          </Box>

          {/* ─── Day Headers ────────────────────────────────────── */}
          <Grid container spacing={0.5}>
            {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((d) => (
              <Grid item xs={12 / 7} key={d}>
                <Typography align="center" variant="body2" fontWeight="bold">{d}</Typography>
              </Grid>
            ))}

            {/* ─── Empty cells before first day ──────────────────── */}
            {Array.from({ length: firstDay }).map((_, i) => (
              <Grid item xs={12 / 7} key={`empty-${i}`} />
            ))}

            {/* ─── Day Cells ────────────────────────────────────── */}
            {days.map((day) => {
              const status = getStatus(day);
              const dayMeetings = getMeetingsForDay(day);
              const groupStatus = getGroupStatusForDay(day);
              const freeCount = groupStatus.filter((g) => g.status === "free").length;
              const busyCount = groupStatus.filter((g) => g.status === "busy").length;
              const maybeCount = groupStatus.filter((g) => g.status === "maybe").length;
              const meetingCount = dayMeetings.length;

              return (
                <Grid item xs={12 / 7} key={day}>
                  {isMobile ? (
                    /* ── Mobile: compact cell, tap to expand ── */
                    <Box
                      onClick={() => handleDayClick(day)}
                      sx={{
                        border: 1,
                        borderColor: status !== "unknown" ? STATUS_COLORS[status] + "60" : "divider",
                        borderRadius: 1.5,
                        p: 0.25,
                        minHeight: 48,
                        bgcolor: STATUS_COLORS[status] + "15",
                        cursor: "pointer",
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        justifyContent: "flex-start",
                        pt: 0.5,
                        transition: "all 0.1s ease",
                        "&:active": { transform: "scale(0.95)", bgcolor: "action.hover" },
                      }}
                    >
                      <Typography
                        sx={{
                          fontWeight: 600,
                          fontSize: "0.75rem",
                          lineHeight: 1.2,
                          color: status !== "unknown" ? STATUS_COLORS[status] : "text.primary",
                        }}
                      >
                        {day}
                      </Typography>

                      {/* Status dot indicator */}
                      <Box
                        sx={{
                          width: 6,
                          height: 6,
                          borderRadius: "50%",
                          mt: 0.25,
                          bgcolor: STATUS_COLORS[status],
                          opacity: status !== "unknown" ? 1 : 0.25,
                        }}
                      />

                      {/* Meeting count badge */}
                      {meetingCount > 0 && (
                        <Box
                          sx={{
                            mt: 0.25,
                            px: 0.6,
                            py: 0.1,
                            borderRadius: 1,
                            bgcolor: "primary.main",
                            color: "white",
                            fontSize: "0.625rem",
                            fontWeight: 700,
                            lineHeight: 1.3,
                          }}
                        >
                          {meetingCount}
                        </Box>
                      )}
                    </Box>
                  ) : (
                    /* ── Desktop: full-featured cell ── */
                    <Box
                      onMouseDown={() => !dragActive && setPendingChanges({})}
                      onMouseUp={handleDragEnd}
                      sx={{
                        border: 1, borderColor: dragActive && pendingChanges[`${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`] ? `${STATUS_COLORS[pendingChanges[`${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`]]}80` : "divider",
                        borderWidth: dragActive && pendingChanges[`${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`] ? 2 : 1,
                        borderRadius: 1,
                        p: 0.5,
                        minHeight: 100,
                        bgcolor: STATUS_COLORS[status] + "15",
                        position: "relative",
                        display: "flex",
                        flexDirection: "column",
                      }}
                    >
                      <Typography variant="body2" fontWeight="bold" sx={{ mb: 0.25, fontSize: "0.875rem" }}>
                        {day}
                      </Typography>

                      {/* Desktop: Drag-to-select buttons */}
                      <Box sx={{ display: "flex", gap: 0.2, mb: 0.3 }}
                        onMouseEnter={() => handleDragEnter(day)}
                      >
                        {(["free", "busy", "maybe"] as string[]).map((s) => {
                          const isSelected = status === s || (dragActive && dragStatus === s);
                          return (
                            <Button
                              key={s}
                              size="small"
                              variant={isSelected ? "contained" : "text"}
                              onMouseDown={(e) => { e.stopPropagation(); handleDragStart(day, s); }}
                              sx={{
                                minWidth: 28, p: "1px 3px", fontSize: 9, lineHeight: 1.2,
                                color: isSelected ? "white" : STATUS_COLORS[s],
                                bgcolor: isSelected ? STATUS_COLORS[s] : "transparent",
                                "&:hover": { bgcolor: isSelected ? STATUS_COLORS[s] : STATUS_COLORS[s] + "20" },
                              }}
                            >
                              {s === "free" ? "F" : s === "busy" ? "B" : "M"}
                            </Button>
                          );
                        })}
                      </Box>

                      {/* Desktop: Group availability summary */}
                      {groupStatus.length > 0 && (
                        <Box sx={{ display: "flex", gap: 0.3, flexWrap: "wrap", mb: 0.3 }}>
                          {freeCount > 0 && (
                            <Tooltip title={`${freeCount} free`}>
                              <Chip label={freeCount} size="small" sx={{ height: 16, minWidth: 16, fontSize: 9, bgcolor: "#4caf50", color: "white" }} />
                            </Tooltip>
                          )}
                          {busyCount > 0 && (
                            <Tooltip title={`${busyCount} busy`}>
                              <Chip label={busyCount} size="small" sx={{ height: 16, minWidth: 16, fontSize: 9, bgcolor: "#f44336", color: "white" }} />
                            </Tooltip>
                          )}
                          {maybeCount > 0 && (
                            <Tooltip title={`${maybeCount} maybe`}>
                              <Chip label={maybeCount} size="small" sx={{ height: 16, minWidth: 16, fontSize: 9, bgcolor: "#ff9800", color: "white" }} />
                            </Tooltip>
                          )}
                        </Box>
                      )}

                      {/* Desktop: Meetings */}
                      {dayMeetings.length > 0 && (
                        <Box sx={{ mt: "auto" }}>
                          {dayMeetings.slice(0, 2).map((m) => (
                            <Chip
                              key={m.id}
                              icon={<Event sx={{ fontSize: 11 }} />}
                              label={m.title}
                              size="small"
                              variant="outlined"
                              color="primary"
                              onClick={() => handleMeetingClick(m)}
                              sx={{ height: 18, fontSize: 9, mb: 0.15, maxWidth: "100%",
                                "& .MuiChip-label": { overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }
                              }}
                            />
                          ))}
                          {dayMeetings.length > 2 && (
                            <Typography variant="caption" color="text.secondary" sx={{ fontSize: 9 }}>+{dayMeetings.length - 2} more</Typography>
                          )}
                        </Box>
                      )}
                    </Box>
                  )}
                </Grid>
              );
            })}
          </Grid>

          {/* Quick actions (desktop) */}
          {!isMobile && (
            <Box sx={{ display: "flex", gap: 1, mt: 1.5, justifyContent: "center", flexWrap: "wrap" }}>
              <Typography variant="caption" color="text.secondary" sx={{ mr: 0.5, alignSelf: "center" }}>
                Quick:
              </Typography>
              <Button size="small" variant="outlined" sx={{ fontSize: 11, py: 0.25, color: "#4caf50", borderColor: "#4caf50" }}
                onClick={() => applyWeekPattern("free")}>
                Free month
              </Button>
              <Button size="small" variant="outlined" sx={{ fontSize: 11, py: 0.25, color: "#f44336", borderColor: "#f44336" }}
                onClick={() => applyWeekPattern("busy")}>
                Busy month
              </Button>
              <Button size="small" variant="outlined" sx={{ fontSize: 11, py: 0.25, color: "#ff9800", borderColor: "#ff9800" }}
                onClick={() => applyWeekPattern("maybe")}>
                Maybe month
              </Button>
            </Box>
          )}

          {/* Legend */}
          <Box sx={{ display: "flex", gap: 2, mt: 1.5, justifyContent: "center", flexWrap: "wrap" }}>
            <Chip label="Free" sx={{ bgcolor: "#4caf50", color: "white", fontSize: 12 }} size="small" />
            <Chip label="Busy" sx={{ bgcolor: "#f44336", color: "white", fontSize: 12 }} size="small" />
            <Chip label="Maybe" sx={{ bgcolor: "#ff9800", color: "white", fontSize: 12 }} size="small" />
            <Chip label="Not Marked" sx={{ bgcolor: "#9e9e9e", color: "white", fontSize: 12 }} size="small" />
          </Box>
        </CardContent>
      </Card>

      {/* ─── Day Detail Bottom Sheet (Mobile) ──────────────────── */}
      <Drawer
        anchor="bottom"
        open={dayDetailOpen}
        onClose={() => setDayDetailOpen(false)}
        PaperProps={{
          sx: {
            maxHeight: "85vh",
            borderTopLeftRadius: 20,
            borderTopRightRadius: 20,
            px: 0,
          },
        }}
      >
        {selectedDay !== null && (() => {
          const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(selectedDay).padStart(2, "0")}`;
          const status = getStatus(selectedDay);
          const dayMeetings = getMeetingsForDay(selectedDay);
          const groupStatus = getGroupStatusForDay(selectedDay);
          const freeCount = groupStatus.filter((g) => g.status === "free").length;
          const busyCount = groupStatus.filter((g) => g.status === "busy").length;
          const maybeCount = groupStatus.filter((g) => g.status === "maybe").length;

          return (
            <Box sx={{ overflow: "auto", px: 2.5, pb: 3, pt: 2 }}>
              {/* Drag handle */}
              <Box sx={{ display: "flex", justifyContent: "center", mb: 2 }}>
                <Box sx={{ width: 36, height: 4, borderRadius: 2, bgcolor: "divider" }} />
              </Box>

              {/* Date header */}
              <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 3 }}>
                <Box sx={{ width: 12, height: 12, borderRadius: "50%", bgcolor: STATUS_COLORS[status], flexShrink: 0 }} />
                <Typography variant="h6" sx={{ fontWeight: 700, fontSize: "1.125rem" }}>
                  {new Date(dateStr).toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })}
                </Typography>
              </Box>

              {/* Availability toggle — large touch-friendly */}
              <Typography variant="subtitle2" sx={{ mb: 1.5, fontWeight: 600, fontSize: "0.8125rem", color: "text.secondary", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                Your Availability
              </Typography>
              <Box sx={{ display: "flex", gap: 1, mb: 3 }}>
                {(["free", "busy", "maybe"] as string[]).map((s) => {
                  const colorMap: Record<string, string> = { free: "#4caf50", busy: "#f44336", maybe: "#ff9800" };
                  const bgMap: Record<string, string> = { free: "#22c55e", busy: "#ef4444", maybe: "#f59e0b" };
                  const isSelected = status === s;
                  return (
                    <Button
                      key={s}
                      variant={isSelected ? "contained" : "outlined"}
                      onClick={() => updateStatus(selectedDay, s)}
                      fullWidth
                      sx={{
                        py: 1.5,
                        fontWeight: 700,
                        fontSize: "0.875rem",
                        borderRadius: 2,
                        color: isSelected ? "white" : colorMap[s],
                        borderColor: isSelected ? "transparent" : colorMap[s] + "60",
                        bgcolor: isSelected ? bgMap[s] : "transparent",
                        "&:hover": { bgcolor: isSelected ? bgMap[s] : colorMap[s] + "15" },
                      }}
                    >
                      {s === "free" ? "✓ Free" : s === "busy" ? "✕ Busy" : "~ Maybe"}
                    </Button>
                  );
                })}
              </Box>

              {/* Group availability */}
              <Typography variant="subtitle2" sx={{ mb: 1.5, fontWeight: 600, fontSize: "0.8125rem", color: "text.secondary", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                Group ({groupStatus.length} marked)
              </Typography>
              {groupStatus.length > 0 ? (
                <Box sx={{ mb: 3 }}>
                  {freeCount > 0 && (
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="caption" sx={{ color: "#4caf50", fontWeight: 600, mb: 0.5, display: "block" }}>
                        Free ({freeCount})
                      </Typography>
                      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
                        {groupStatus.filter((g) => g.status === "free").map((g) => (
                          <Chip key={g.user_id} label={g.name} size="small" sx={{ bgcolor: "#4caf50" + "20", color: "#4caf50", fontWeight: 500 }} />
                        ))}
                      </Box>
                    </Box>
                  )}
                  {busyCount > 0 && (
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="caption" sx={{ color: "#f44336", fontWeight: 600, mb: 0.5, display: "block" }}>
                        Busy ({busyCount})
                      </Typography>
                      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
                        {groupStatus.filter((g) => g.status === "busy").map((g) => (
                          <Chip key={g.user_id} label={g.name} size="small" sx={{ bgcolor: "#f44336" + "20", color: "#f44336", fontWeight: 500 }} />
                        ))}
                      </Box>
                    </Box>
                  )}
                  {maybeCount > 0 && (
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="caption" sx={{ color: "#ff9800", fontWeight: 600, mb: 0.5, display: "block" }}>
                        Maybe ({maybeCount})
                      </Typography>
                      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
                        {groupStatus.filter((g) => g.status === "maybe").map((g) => (
                          <Chip key={g.user_id} label={g.name} size="small" sx={{ bgcolor: "#ff9800" + "20", color: "#ff9800", fontWeight: 500 }} />
                        ))}
                      </Box>
                    </Box>
                  )}
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                  No one has marked availability for this day yet.
                </Typography>
              )}

              {/* Meetings on this day */}
              <Typography variant="subtitle2" sx={{ mb: 1.5, fontWeight: 600, fontSize: "0.8125rem", color: "text.secondary", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                Events ({dayMeetings.length})
              </Typography>
              {dayMeetings.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  No events scheduled for this day.
                </Typography>
              ) : (
                <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                  {dayMeetings.map((m) => {
                    const myRsvp = findMyRsvp(m);
                    return (
                      <Card
                        key={m.id}
                        variant="outlined"
                        sx={{ borderRadius: 2, boxShadow: "none", "&:hover": { boxShadow: "none" } }}
                      >
                        <CardContent sx={{ p: 2, "&:last-child": { pb: 2 } }}>
                          <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", mb: 0.5 }}>
                            <Typography variant="body2" fontWeight={600}>{m.title}</Typography>
                            <IconButton size="small" color="error" onClick={() => handleDeleteMeeting(m.id)} sx={{ ml: 1, mt: -0.5 }}>
                              <Delete fontSize="small" />
                            </IconButton>
                          </Box>
                          {m.time && <Typography variant="caption" color="text.secondary" display="block">🕐 {m.time}</Typography>}
                          {m.location && <Typography variant="caption" color="text.secondary" display="block">📍 {m.location}</Typography>}
                          {m.description && <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>{m.description}</Typography>}
                          {/* Inline RSVP */}
                          <Box sx={{ display: "flex", gap: 0.5, mt: 1 }}>
                            {(["going", "maybe", "not_going"] as RsvpStatus[]).map((s) => {
                              const isSelected = myRsvp === s;
                              const colorMap = { going: "success", maybe: "warning", not_going: "error" } as const;
                              return (
                                <Button
                                  key={s}
                                  size="small"
                                  variant={isSelected ? "contained" : "outlined"}
                                  color={colorMap[s]}
                                  onClick={() => handleRsvp(s, m.id)}
                                  sx={{ flex: 1, fontSize: "0.7rem", py: 0.5, minHeight: 0 }}
                                >
                                  {s === "going" ? "✓" : s === "not_going" ? "✕" : "?"}
                                </Button>
                              );
                            })}
                          </Box>
                        </CardContent>
                      </Card>
                    );
                  })}
                </Box>
              )}

              <Button onClick={() => setDayDetailOpen(false)} fullWidth variant="outlined" sx={{ mt: 2 }}>
                Close
              </Button>
            </Box>
          );
        })()}
      </Drawer>

      {/* ─── Meeting Detail Dialog ─────────────────────────────── */}
      <Dialog open={meetingDialogOpen} onClose={() => { setMeetingDialogOpen(false); setSelectedMeeting(null); }} maxWidth="sm" fullWidth>
        {selectedMeeting && (
          <>
            <DialogTitle sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <Box>
                <Event sx={{ mr: 1, verticalAlign: "middle" }} />
                {selectedMeeting.title}
              </Box>
              <IconButton
                size="small"
                color="error"
                onClick={() => handleDeleteMeeting(selectedMeeting.id)}
                title="Delete event"
              >
                <Delete />
              </IconButton>
            </DialogTitle>
            <DialogContent dividers>
              {selectedMeeting.idea_title && (
                <Chip
                  label={`From idea: ${selectedMeeting.idea_title}`}
                  size="small"
                  color="secondary"
                  variant="outlined"
                  sx={{ mb: 1 }}
                />
              )}
              {selectedMeeting.description && (
                <Typography variant="body1" sx={{ mb: 2 }}>{selectedMeeting.description}</Typography>
              )}
              <Typography variant="body2" color="text.secondary">
                <strong>Date:</strong> {selectedMeeting.date}
                {selectedMeeting.time && <> at {selectedMeeting.time}</>}
              </Typography>
              {selectedMeeting.location && (
                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                  <strong>Location:</strong> {selectedMeeting.location}
                </Typography>
              )}
              {selectedMeeting.creator_name && (
                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                  <strong>Proposed by:</strong> {selectedMeeting.creator_name}
                </Typography>
              )}

              {/* RSVP section */}
              <Box sx={{ mt: 3, mb: 2 }}>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>Your RSVP</Typography>
                <Box sx={{ display: "flex", flexDirection: { xs: "column", sm: "row" }, gap: 0.5 }}>
                  {(["going", "maybe", "not_going"] as RsvpStatus[]).map((s) => {
                    const myStatus = findMyRsvp(selectedMeeting!);
                    const isSelected = rsvpStatus === s || myStatus === s;
                    const colorMap: Record<RsvpStatus, string> = {
                      going: "success",
                      maybe: "warning",
                      not_going: "error",
                    };
                    return (
                      <Button
                        key={s}
                        variant={isSelected ? "contained" : "outlined"}
                        color={colorMap[s] as "success" | "warning" | "error"}
                        size="small"
                        disabled={rsvpLoading}
                        onClick={() => handleRsvp(s, selectedMeeting!.id)}
                      >
                        {RSVP_LABELS[s]}
                      </Button>
                    );
                  })}
                </Box>
              </Box>

              {/* Participant summary */}
              {selectedMeeting.participants && selectedMeeting.participants.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" sx={{ mb: 1 }}>Participants</Typography>
                  {(["going", "maybe", "not_going"] as RsvpStatus[]).map((s) => {
                    const filtered = selectedMeeting!.participants.filter((p) => p.status === s);
                    if (filtered.length === 0) return null;
                    const colorMap: Record<RsvpStatus, string> = {
                      going: "#4caf50",
                      maybe: "#ff9800",
                      not_going: "#f44336",
                    };
                    return (
                      <Box key={s} sx={{ mb: 1 }}>
                        <Typography variant="caption" sx={{ color: colorMap[s], fontWeight: "bold" }}>
                          {RSVP_LABELS[s]} ({filtered.length})
                        </Typography>
                        <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5, mt: 0.3 }}>
                          {filtered.map((p) => (
                            <Chip
                              key={p.user_id}
                              label={p.user_name}
                              size="small"
                              sx={{ bgcolor: colorMap[s] + "22", color: colorMap[s], fontWeight: "medium" }}
                            />
                          ))}
                        </Box>
                      </Box>
                    );
                  })}
                </Box>
              )}
            </DialogContent>
            <DialogActions>
              <Button onClick={() => { setMeetingDialogOpen(false); setSelectedMeeting(null); }}>Close</Button>
            </DialogActions>
          </>
        )}
      </Dialog>

      {/* ─── Create Meeting Dialog ─────────────────────────────── */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Propose Event</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Title"
            fullWidth
            required
            value={newMeeting.title}
            onChange={(e) => setNewMeeting((prev) => ({ ...prev, title: e.target.value }))}
          />
          <TextField
            margin="dense"
            label="Description"
            fullWidth
            multiline
            rows={3}
            value={newMeeting.description}
            onChange={(e) => setNewMeeting((prev) => ({ ...prev, description: e.target.value }))}
          />
          <TextField
            margin="dense"
            label="Date"
            type="date"
            fullWidth
            required
            value={createDate}
            onChange={(e) => setCreateDate(e.target.value)}
            InputLabelProps={{ shrink: true }}
            sx={{ mt: 1 }}
          />
          <TextField
            margin="dense"
            label="Time"
            type="time"
            fullWidth
            value={newMeeting.time}
            onChange={(e) => setNewMeeting((prev) => ({ ...prev, time: e.target.value }))}
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            margin="dense"
            label="Location"
            fullWidth
            value={newMeeting.location}
            onChange={(e) => setNewMeeting((prev) => ({ ...prev, location: e.target.value }))}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreateMeeting}>Create Event</Button>
        </DialogActions>
      </Dialog>

      {/* ─── Snackbar ──────────────────────────────────────────── */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar((prev) => ({ ...prev, open: false }))}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert severity={snackbar.severity} variant="filled">
          {snackbar.message}
        </Alert>
      </Snackbar>
    </>
  );
};

export default CalendarPage;
