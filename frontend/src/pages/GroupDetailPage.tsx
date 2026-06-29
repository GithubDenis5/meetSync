import React, { useState, useEffect } from "react";
import {
  Box, Typography, Card, CardContent, Tabs, Tab, Chip, Button,
  CircularProgress, List, ListItem, ListItemText, Avatar,
  Dialog, DialogTitle, DialogContent, DialogActions, TextField, Alert,
  useMediaQuery,
} from "@mui/material";
import { useParams, useNavigate } from "react-router-dom";
import { groupApi } from "../utils/api";
import { Group, Member } from "../types";
import { ContentCopy } from "@mui/icons-material";

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
  const isMobile = useMediaQuery("(max-width:600px)");

  useEffect(() => {
    if (!id) return;
    Promise.all([
      groupApi.get(Number(id)).then(({ data }) => setGroup(data)),
      groupApi.members(Number(id)).then(({ data }) => setMembers(data)),
    ]).catch(() => navigate("/groups")).finally(() => setLoading(false));
  }, [id]);

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
          <Tab label="Settings" />
        </Tabs>

        <TabPanel value={tab} index={0}>
          <List>
            {members.map((m) => (
              <ListItem key={m.id}>
                <Avatar sx={{ mr: 2 }}>{m.name[0]}</Avatar>
                <ListItemText primary={m.name} secondary={m.username ? `@${m.username}` : m.role} />
                <Chip label={m.role} color={m.role === "OWNER" ? "primary" : m.role === "ADMIN" ? "secondary" : "default"} size="small" />
              </ListItem>
            ))}
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
