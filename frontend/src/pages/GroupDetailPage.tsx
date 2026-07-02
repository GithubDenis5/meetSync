import React, { useState, useEffect } from "react";
import {
  Box, Typography, Card, CardContent, Tabs, Tab, Chip, Button,
  CircularProgress, List, ListItem, ListItemText, Avatar,
  Dialog, DialogTitle, DialogContent, DialogActions, TextField, Alert,
  useMediaQuery, LinearProgress,
} from "@mui/material";
import { useParams, useNavigate } from "react-router-dom";
import { groupApi } from "../utils/api";
import { Group, Member, GroupDashboard } from "../types";
import { ContentCopy, Assessment, FiberManualRecord } from "@mui/icons-material";

interface TabPanelProps {
  children: React.ReactNode;
  value: number;
  index: number;
}
const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div hidden={value !== index}>{value === index && <Box sx={{ pt: 3 }}>{children}</Box>}</div>
);

const GroupDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [group, setGroup] = useState<Group | null>(null);
  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState(0);
  const [error, setError] = useState("");
  const [dashboard, setDashboard] = useState<GroupDashboard | null>(null);
  const [dashboardLoading, setDashboardLoading] = useState(false);
  const [onlineUsers, setOnlineUsers] = useState<number[]>([]);
  const isMobile = useMediaQuery("(max-width:600px)");

  useEffect(() => {
    if (!id) return;
    Promise.all([
      groupApi.get(Number(id)).then(({ data }) => setGroup(data)),
      groupApi.members(Number(id)).then(({ data }) => setMembers(data)),
    ]).catch(() => navigate("/groups")).finally(() => setLoading(false));
  }, [id]);

  // Load dashboard when tab changes to Dashboard (index 4)
  useEffect(() => {
    if (tab === 4 && id) {
      setDashboardLoading(true);
      groupApi.dashboard(Number(id))
        .then(({ data }) => setDashboard(data))
        .catch(() => setError("Failed to load dashboard"))
        .finally(() => setDashboardLoading(false));
    }
  }, [tab, id]);

  // Poll online members every 30s when on Participants tab
  useEffect(() => {
    if (tab !== 0 || !id) return;
    const fetchOnline = () => {
      groupApi.onlineMembers(Number(id))
        .then(({ data }) => setOnlineUsers(data.online_user_ids))
        .catch(() => {});
    };
    fetchOnline();
    const interval = setInterval(fetchOnline, 30000);
    return () => clearInterval(interval);
  }, [tab, id]);

  if (loading) return <Box sx={{ display: "flex", justifyContent: "center", mt: 4 }}><CircularProgress /></Box>;
  if (!group) return <Typography>Group not found</Typography>;

  return (
    <>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" gutterBottom sx={{ fontSize: { xs: "1.5rem", sm: "2rem" } }}>{group.name}</Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 1 }}>
          {group.description || "No description"}
        </Typography>
        <Box sx={{ display: "flex", gap: 1, alignItems: "center", flexWrap: "wrap" }}>
          <Chip
            icon={<ContentCopy fontSize="small" />}
            label={`Invite: ${group.invite_code}`}
            onClick={() => navigator.clipboard.writeText(group.invite_code)}
            size="small"
          />
          <Chip label={`Min people: ${group.min_people_for_meeting}`} variant="outlined" size="small" />
        </Box>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Card>
        <Tabs value={tab} onChange={(_, v) => setTab(v)}
          variant={isMobile ? "scrollable" : "standard"}
          scrollButtons={isMobile ? "auto" : undefined}
        >
          <Tab label="Participants" />
          <Tab label="Group Calendar" />
          <Tab label="Ideas" />
          <Tab label="Meetings" />
          <Tab label="Dashboard" icon={<Assessment sx={{ fontSize: 18 }} />} iconPosition="start" />
          <Tab label="Settings" />
        </Tabs>

        <TabPanel value={tab} index={0}>
          <List>
            {members.map((m) => {
              const isOnline = onlineUsers.includes(m.user_id);
              return (
                <ListItem key={m.id}>
                  <Box sx={{ position: "relative", mr: 2 }}>
                    <Avatar>{m.name[0]}</Avatar>
                    {isOnline && (
                      <FiberManualRecord
                        sx={{
                          fontSize: 12, color: "#4caf50",
                          position: "absolute", bottom: -2, right: -2,
                          bgcolor: "background.paper",
                          borderRadius: "50%",
                        }}
                      />
                    )}
                  </Box>
                  <ListItemText
                    primary={
                      <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                        {m.name}
                        {isOnline && (
                          <Typography variant="caption" sx={{ color: "#4caf50", fontSize: 10 }}>
                            online
                          </Typography>
                        )}
                      </Box>
                    }
                    secondary={m.username ? `@${m.username}` : m.role}
                  />
                  <Chip label={m.role} color={m.role === "OWNER" ? "primary" : m.role === "ADMIN" ? "secondary" : "default"} size="small" />
                </ListItem>
              );
            })}
          </List>
        </TabPanel>

        <TabPanel value={tab} index={1}>
          <Typography color="text.secondary">
            Group calendar view — see when everyone is available.
          </Typography>
          <Button variant="outlined" sx={{ mt: 2 }} onClick={() => navigate("/calendar")}>
            Open Calendar
          </Button>
        </TabPanel>

        <TabPanel value={tab} index={2}>
          <Typography color="text.secondary" sx={{ mb: 2 }}>
            Group idea bank — suggest and vote on activities.
          </Typography>
          <Button variant="outlined" onClick={() => navigate(`/ideas?group_id=${group.id}`)}>
            View Ideas
          </Button>
        </TabPanel>

        <TabPanel value={tab} index={3}>
          <Typography color="text.secondary">
            Meeting history for this group will appear here.
          </Typography>
        </TabPanel>

        <TabPanel value={tab} index={4}>
          {dashboardLoading ? (
            <Box sx={{ display: "flex", justifyContent: "center", p: 4 }}><CircularProgress /></Box>
          ) : dashboard ? (
            <Box>
              {/* Summary cards */}
              <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", mb: 3 }}>
                <Card variant="outlined" sx={{ flex: "1 1 140px" }}>
                  <CardContent sx={{ p: 2, textAlign: "center" }}>
                    <Typography variant="h4" color="primary">{dashboard.total_members}</Typography>
                    <Typography variant="caption" color="text.secondary">Members</Typography>
                  </CardContent>
                </Card>
                <Card variant="outlined" sx={{ flex: "1 1 140px" }}>
                  <CardContent sx={{ p: 2, textAlign: "center" }}>
                    <Typography variant="h4" color="primary">{dashboard.total_meetings}</Typography>
                    <Typography variant="caption" color="text.secondary">Meetings</Typography>
                  </CardContent>
                </Card>
                <Card variant="outlined" sx={{ flex: "1 1 140px" }}>
                  <CardContent sx={{ p: 2, textAlign: "center" }}>
                    <Typography variant="h4" color="primary">{dashboard.average_attendance}</Typography>
                    <Typography variant="caption" color="text.secondary">Avg Attendance</Typography>
                  </CardContent>
                </Card>
                <Card variant="outlined" sx={{ flex: "1 1 140px" }}>
                  <CardContent sx={{ p: 2, textAlign: "center" }}>
                    <Typography variant="h4" color="primary">{dashboard.upcoming_meetings}</Typography>
                    <Typography variant="caption" color="text.secondary">Upcoming</Typography>
                  </CardContent>
                </Card>
                <Card variant="outlined" sx={{ flex: "1 1 140px" }}>
                  <CardContent sx={{ p: 2, textAlign: "center" }}>
                    <Typography variant="h4" color="primary">{dashboard.availability_pct}%</Typography>
                    <Typography variant="caption" color="text.secondary">Availability</Typography>
                  </CardContent>
                </Card>
              </Box>

              {/* Top ideas */}
              {dashboard.top_ideas.length > 0 && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>Top Ideas</Typography>
                  {dashboard.top_ideas.map((idea, i) => (
                    <Box key={idea.id} sx={{ display: "flex", alignItems: "center", gap: 1, mb: 0.5 }}>
                      <Chip label={i + 1} size="small" color="primary" sx={{ minWidth: 28 }} />
                      <Typography variant="body2" sx={{ flex: 1 }}>{idea.title}</Typography>
                      <Chip label={`${idea.reactions} reactions`} size="small" variant="outlined" />
                    </Box>
                  ))}
                </Box>
              )}

              {/* Member availability */}
              {dashboard.member_availability.length > 0 && (
                <Box>
                  <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>Member Availability (next 14 days)</Typography>
                  {dashboard.member_availability.map((m) => {
                    const pct = m.free_days > 0 ? Math.round((m.free_days / 14) * 100) : 0;
                    return (
                      <Box key={m.user_id} sx={{ mb: 1 }}>
                        <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.25 }}>
                          <Typography variant="caption">{m.user_name}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {m.free_days}/14 free · {m.marked_days} marked
                          </Typography>
                        </Box>
                        <LinearProgress
                          variant="determinate"
                          value={pct}
                          sx={{ height: 6, borderRadius: 3, bgcolor: "action.hover",
                            "& .MuiLinearProgress-bar": { bgcolor: pct > 50 ? "#4caf50" : pct > 25 ? "#ff9800" : "#f44336" }
                          }}
                        />
                      </Box>
                    );
                  })}
                </Box>
              )}
            </Box>
          ) : (
            <Typography color="text.secondary">Dashboard data unavailable.</Typography>
          )}
        </TabPanel>

        <TabPanel value={tab} index={5}>
          <Typography color="text.secondary" sx={{ mb: 2 }}>
            Group settings and member management.
          </Typography>
          {members
            .filter((m) => m.role === "OWNER" || m.role === "ADMIN")
            .map((m) => (
              <Typography key={m.id} variant="body2">
                {m.name} — {m.role}
              </Typography>
            ))}
        </TabPanel>
      </Card>
    </>
  );
};

export default GroupDetailPage;
