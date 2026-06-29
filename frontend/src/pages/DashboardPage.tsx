import React, { useState, useEffect } from "react";
import {
  Grid, Card, CardContent, Typography, List, ListItem,
  ListItemButton, ListItemText, Chip, Box, CircularProgress,
} from "@mui/material";
import { Group, HowToVote, Lightbulb, CalendarMonth } from "@mui/icons-material";
import { groupApi } from "../utils/api";
import { Group as GroupType } from "../types";
import { useNavigate } from "react-router-dom";

const DashboardPage: React.FC = () => {
  const [groups, setGroups] = useState<GroupType[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    groupApi.list().then(({ data }) => setGroups(data)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <Box sx={{ display: "flex", justifyContent: "center", mt: 4 }}><CircularProgress /></Box>;

  return (
    <>
      <Typography variant="h4" gutterBottom>Dashboard</Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
                <Group color="primary" />
                <Typography variant="h6">My Groups</Typography>
              </Box>
              <Typography variant="h3">{groups.length}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
                <HowToVote color="secondary" />
                <Typography variant="h6">Active Votes</Typography>
              </Box>
              <Typography variant="h3">0</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md="auto">
          <Card>
            <CardContent>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
                <Lightbulb color="warning" />
                <Typography variant="h6">Ideas</Typography>
              </Box>
              <Typography variant="h3">0</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md="auto">
          <Card>
            <CardContent>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
                <CalendarMonth color="success" />
                <Typography variant="h6">Meetings</Typography>
              </Box>
              <Typography variant="h3">0</Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>My Groups</Typography>
              {groups.length === 0 ? (
                <Typography color="text.secondary">No groups yet. Create one!</Typography>
              ) : (
                <List>
                  {groups.map((g) => (
                    <ListItem key={g.id} disablePadding>
                      <ListItemButton onClick={() => navigate(`/groups/${g.id}`)}>
                        <ListItemText primary={g.name} secondary={`Code: ${g.invite_code}`} />
                        <Chip label={g.description || "No description"} size="small" />
                      </ListItemButton>
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Recent Activity</Typography>
              <Typography color="text.secondary">
                No recent activity. Join or create a group to get started!
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </>
  );
};

export default DashboardPage;
